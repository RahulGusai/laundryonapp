import copy
import json
from typing import List
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from enums import NotificationType, OrderCategory, OrderStatus, PaymentStatus
import firebase_service
import models
import math
import schemas
from pricing_store import pricing_store
from schemas import OrderCreate, OrderDetails, OrderFulfillment, OrderUpdate
import address_service
import boto3
import stripe


S3_ACCESS_KEY = "DO00NL6AQYZN9L4PJFAZ"
S3_SECRET_KEY = "VKTAtZabkmpiu1Af0F3uLqBekbhSg6rpGjwROTshFMg"
S3_BUCKET_NAME = "order-images"
S3_REGION = "nyc3"
S3_ENDPOINT_URL = "https://nyc3.digitaloceanspaces.com"


def place_order(db: Session, customer_id: int, order_create: OrderCreate):
    customer_address = address_service.get_customer_address_by_id(
        db, order_create.customer_address_id)

    db_order = models.Order(category=order_create.category,
                            details=order_create.details.to_dict(), pickup_time=order_create.pickup_time, dropoff_time=order_create.dropoff_time, customer_address=customer_address.to_dict(), payment_status=PaymentStatus.PAYMENT_INITIALIZED, order_status=OrderStatus.ORDER_CREATED, customer_id=customer_id)
    db.add(db_order)
    db.commit()
    return db_order


def create_payment_intent(db: Session, order_id: int):
    db_order = get_order_by_id(db, order_id)

    revised_weight = db_order.order_meta["revised_weight"] if "revised_weight" in db_order.order_meta else None
    amount = get_amount_for_order(
        db_order.category, db_order.details, revised_weight)
    amount = amount*100
    amount += ((amount*20)/100)

    payment_intent = stripe.PaymentIntent.create(
        amount=math.ceil(amount),
        currency='cad',
        payment_method_types=["card"],
        payment_method_options={"card": {"capture_method": "manual"}},
        metadata={
            "order_id": db_order.id
        }
    )

    db_order_payment = models.OrderPayment(
        payment_intent=payment_intent, order_id=db_order.id)
    db.add(db_order_payment)
    db.commit()

    # Send push notification to the customer
    notification_data = {
        "type": NotificationType.PAYMENT_INTENT_CREATED,
        "data": {
            "order_id": order_id
        }
    }
    firebase_service.send_push_notification_to_customer(
        db, db_order.customer_id, notification_data=notification_data)

    return {"order_id": order_id, "client_secret": payment_intent['client_secret']}


def get_order_by_id(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def get_amount_for_order(order_category: OrderCategory, order_detail: schemas.OrderDetails, updated_weight=None):
    if order_category == OrderCategory.LAUNDRY:
        min_amount = 20
        min_weight = 10
        amount_per_pound = 2.1

        if updated_weight:
            order_weight = updated_weight
        else:
            order_weight = order_detail.weight

        if not order_weight:
            raise HTTPException(
                status_code=400, detail="Weight of the order not present in order details.")

        if order_weight <= min_weight:
            return min_amount
        else:
            weight_above_threshold = order_weight-min_weight
            return math.ceil(min_amount + (weight_above_threshold*amount_per_pound))

    if order_category == OrderCategory.ONLY_IRON:
        order_items_dict = order_detail.items
        if not order_items_dict:
            raise HTTPException(
                status_code=400, detail="Order items not present in order details.")

        amount = 0
        for item, no_of_item in order_items_dict.items():
            item = item.lower().strip()
            if item not in pricing_store["ironing"]:
                pass

            item_price = pricing_store["ironing"].get(item)
            item_price += 2
            amount += item_price*no_of_item
        return amount

    if order_category == OrderCategory.DRY_CLEAN:
        order_items_dict = order_detail.items
        if not order_items_dict:
            raise HTTPException(
                status_code=400, detail="Order items not present in order details.")

        amount = 0
        for item, no_of_item in order_items_dict.items():
            item = item.lower().strip()
            if item not in pricing_store["dry_clean"]:
                pass

            item_price = pricing_store["dry_clean"].get(item)
            item_price += 2
            amount += item_price*no_of_item
        return amount


def get_customer_orders(db: Session, customer_id: int, payment_status_list: List[PaymentStatus], order_status_list: List[OrderStatus]):
    query = db.query(models.Order).filter(
        models.Order.customer_id == customer_id)
    if payment_status_list:
        query = query.filter(
            models.Order.payment_status.in_(payment_status_list))
    if order_status_list:
        query = query.filter(models.Order.order_status.in_(order_status_list))
    orders = query.all()
    return orders


def update_order_payment_status(db: Session, order_id: int, payment_status: PaymentStatus):
    db_order = db.query(models.Order).filter(
        models.Order.id == order_id).first()
    db_order.payment_status = payment_status
    db.commit()


def get_orders_by_status_in(db: Session, payment_status: List[PaymentStatus], order_status: List[OrderStatus]):
    query = db.query(models.Order)
    if payment_status:
        query = query.filter(models.Order.payment_status.in_(payment_status))
    if order_status:
        query = query.filter(models.Order.order_status.in_(order_status))
    orders = query.all()
    return orders


def update_order(db: Session, order_id: int, order_update: OrderUpdate):
    db_order = db.query(models.Order).filter(
        models.Order.id == order_id).first()
    if db_order is None:
        raise HTTPException(status_code=400, detail="Invalid Order Id.")

    if order_update.order_status:
        db_order.order_status = order_update.order_status

    if order_update.weight:
        updated_order_meta = copy.deepcopy(db_order.order_meta)
        updated_order_meta["revised_weight"] = order_update.weight
        db_order.order_meta = updated_order_meta

    db.commit()
    return db_order


def upload_order_images(db: Session, order_id, images: List[UploadFile]):
    s3 = boto3.client("s3", aws_access_key_id=S3_ACCESS_KEY, aws_secret_access_key=S3_SECRET_KEY,
                      region_name=S3_REGION, endpoint_url=S3_ENDPOINT_URL)
    count = 1
    url_list = []
    for image in images:
        ext = image.filename.split('.')[1]
        file_name = f"order_{order_id}_{count}.{ext}"
        count += 1
        s3.upload_fileobj(image.file, S3_BUCKET_NAME, file_name)
        url_list.append(
            f"https://{S3_BUCKET_NAME}.{S3_REGION}.digitaloceanspaces.com/{file_name}")

    db_order = db.query(models.Order).filter(
        models.Order.id == order_id).first()
    updated_order_meta = db_order.order_meta
    updated_order_meta["images"] = url_list
    db_order.order_meta = updated_order_meta
    db.commit()

    return {"message": "Order images uploaded successfully"}


def begin_fulfillment(db: Session, order_id: int, order_fulfillment: OrderFulfillment):
    db_order = db.query(models.Order).filter(
        models.Order.id == order_id).first()
    if not db_order:
        raise HTTPException(
            status_code=400, detail="No order found for the given order id.")

    order_payment = db_order.order_payment
    if not order_payment:
        raise HTTPException(
            status_code=400, detail="No order payment found for the given order id.")
    payment_intent = order_payment.payment_intent
    if order_fulfillment.amount_to_capture > payment_intent["amount"]:
        return HTTPException(status_code=400, detail="The amount to be captured exceeds the original payment intent amount.")

    stripe.PaymentIntent.capture(
        payment_intent["id"], amount_to_capture=math.ceil(order_fulfillment.amount_to_capture))
    db_order.order_status = OrderStatus.ORDER_FULFILLMENT

    if order_fulfillment.reason:
        updated_order_meta = copy.deepcopy(db_order.order_meta)
        updated_order_meta["reason"] = order_fulfillment.reason
        db_order.order_meta = updated_order_meta

    db.commit()
    return db_order
