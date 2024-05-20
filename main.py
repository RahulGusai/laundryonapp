from typing import List, Optional
from fastapi import Depends, FastAPI, Form, HTTPException, Header, Path, Query, UploadFile
from sqlalchemy.orm import Session
import stripe
import driver_service
from enums import OrderStatus, PaymentStatus, Roles
import laundromart_service
import order_service
import customer_service
from database import SessionLocal, engine
import schemas
import models
import auth_service
from datetime import timedelta
from utils import is_password_correct
import address_service
import firebase_service
import validation_service

models.Base.metadata.create_all(bind=engine)

stripe.api_key = 'sk_test_51OCeU2G8qLogHio9tcIPAyfAQMiTptXAxWQ4gpSd9Tq8NWGDC0cx1hnqSGyMSH8KWor272PzO39MzeHp5ACL2MDp00vDxsMOGT'
app = FastAPI()

# Dependency


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/customer/register/", response_model=schemas.Customer)
def register_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    validation_service.validate_customer_registration(db, customer=customer)
    return customer_service.create_customer(db, customer)


@app.post("/driver/register/", response_model=schemas.Driver)
def register_driver(driver: schemas.DriverCreate, db: Session = Depends(get_db)):
    validation_service.validate_driver_registration(db, driver=driver)
    return driver_service.create_driver(db, driver)


@app.post("/driver/login/")
def login_driver(login_details: schemas.Login, db: Session = Depends(get_db)):
    driver = driver_service.get_driver_by_email(db, login_details.email)
    if not driver:
        raise HTTPException(status_code=400, detail="Invalid email address.")

    if not is_password_correct(login_password=login_details.password, db_passsword=driver.password):
        raise HTTPException(status_code=400, detail="Incorrect password.")

    payload = {"id": driver.id, "role": Roles.DRIVER}
    expires_delta = timedelta(hours=2)
    access_token = auth_service.generate_jwt_token(payload, expires_delta)

    return {"driver_id": driver.id, "access_token": access_token, "token_type": "bearer"}


@app.get("/driver/", response_model=schemas.Driver)
def get_driver_detail(driver_id: int = Depends(auth_service.verify_jwt_token_driver), db: Session = Depends(get_db)):
    return driver_service.get_driver_by_id(db, driver_id)


@app.post("/laundromart/register/", response_model=schemas.LaundroMart)
def register_laundromart(laundromart: schemas.LaundroMartCreate, db: Session = Depends(get_db)):
    validation_service.validate_laundromart_registration(
        db, laundromart=laundromart)
    return laundromart_service.create_laundromart(db, laundromart)


@app.post("/laundromart/login/")
def login_laundromart(login_details: schemas.Login, db: Session = Depends(get_db)):
    laundromart = laundromart_service.get_laundromart_by_email(
        db, login_details.email)
    if not laundromart:
        raise HTTPException(status_code=400, detail="Invalid email address.")

    if not is_password_correct(login_password=login_details.password, db_passsword=laundromart.password):
        raise HTTPException(status_code=400, detail="Incorrect password.")

    payload = {
        "id": laundromart.id, "role": Roles.LAUNDROMART}
    expires_delta = timedelta(hours=48)
    access_token = auth_service.generate_jwt_token(payload, expires_delta)

    return {"laundromart_id": laundromart.id, "access_token": access_token, "token_type": "bearer"}


@app.get("/laundromart/", response_model=schemas.LaundroMart)
def get_laundromart_detail(laundromart_id: int = Depends(auth_service.verify_jwt_token_laundromart), db: Session = Depends(get_db)):
    return laundromart_service.get_laundromart_by_id(db, laundromart_id)


@app.post("/customer/login/")
def login_customer(login_details: schemas.Login, db: Session = Depends(get_db)):
    customer = customer_service.get_customer_by_email(db, login_details.email)
    if not customer:
        raise HTTPException(status_code=400, detail="Invalid email address.")

    if not is_password_correct(login_password=login_details.password, db_passsword=customer.password):
        raise HTTPException(status_code=400, detail="Incorrect password.")

    payload = {"id": customer.id, "role": Roles.CUSTOMER}
    expires_delta = timedelta(hours=48)
    access_token = auth_service.generate_jwt_token(payload, expires_delta)

    return {"customer_id": customer.id, "access_token": access_token, "token_type": "bearer"}


@app.get("/customer/", response_model=schemas.Customer)
def get_customer_detail(customer_id: int = Depends(auth_service.verify_jwt_token_customer), db: Session = Depends(get_db)):
    return customer_service.get_customer_by_id(db, customer_id)


@app.put("/customer/", response_model=schemas.Customer)
def update_customer_detail(updated_customer: schemas.CustomerUpdate, customer_id: int = Depends(auth_service.verify_jwt_token_customer), db: Session = Depends(get_db)):
    return customer_service.update_customer_details(
        db, customer_id=customer_id, updated_customer=updated_customer)


@app.post("/order/")
def place_order(order_create: schemas.OrderCreate, customer_id: int = Depends(auth_service.verify_jwt_token_customer), db: Session = Depends(get_db)):
    return order_service.place_order(db, customer_id, order_create)


@app.post("/order/{order_id}/payment-intent")
def create_payment_intent(order_id: int, driver_id: int = Depends(auth_service.verify_jwt_token_driver), db: Session = Depends(get_db)):
    return order_service.create_payment_intent(db, order_id)


@app.get("/customer/order/", response_model=List[schemas.Order])
def get_customer_orders(payment_status: List[PaymentStatus] = Query([], title="Payment status"), order_status: List[OrderStatus] = Query([], title="Order status"), customer_id: int = Depends(auth_service.verify_jwt_token_customer), db: Session = Depends(get_db)):
    return order_service.get_customer_orders(
        db, customer_id, payment_status, order_status)


@app.post("/stripe/payment-webhook/")
def update_order_payment_status(event_payload: dict, db: Session = Depends(get_db)):
    print("Received a webhook from Stripe")

    event_type = event_payload["type"]
    if event_type is None:
        print("Event type not found in the stripe event's payload..returning")

    event_data_obj = event_payload["data"]["object"]
    order_id = event_data_obj["metadata"]["order_id"]

    if order_id is None:
        print("Order Id not found in the stripe event's payload..returning")

    if event_type == 'payment_intent.amount_capturable_updated':
        return order_service.update_order_payment_status(
            db, order_id, PaymentStatus.PAYMENT_ON_HOLD)

    if event_type == 'payment_intent.succeeded':
        # TODO Update order status to fulfillment here
        return order_service.update_order_payment_status(
            db, order_id, PaymentStatus.PAYMENT_SUCCEEDED)

    if event_type == 'payment_intent.failed' or event_type == 'payment_intent.cancelled':
        return order_service.update_order_payment_status(
            db, order_id, PaymentStatus.PAYMENT_FAILED)

    print("Unhandled stripe event's type..returning")


@app.get("/order/", response_model=List[schemas.Order])
def get_orders_by_status_in(id: int = Depends(auth_service.verify_jwt_token_get_orders), payment_status: List[PaymentStatus] = Query([], title="Payment status"), order_status: List[OrderStatus] = Query([], title="Order status"), db: Session = Depends(get_db)):
    return order_service.get_orders_by_status_in(db, payment_status, order_status)


@app.put("/laundromart/accept-order/{order_id}")
def accept_order_by_laundromart(order_id: int = Path(..., title="Id of order being accepted"), laundromart_id: int = Depends(auth_service.verify_jwt_token_laundromart), db: Session = Depends(get_db)):
    db_order = order_service.get_order_by_id(db, order_id)
    if not db_order:
        raise HTTPException(status_code=400, detail="Invalid Order Id.")

    db_order.order_status = OrderStatus.LAUNDROMART_ACCEPTED
    db_order.laundromart_id = laundromart_id
    db.commit()
    return db_order


@app.put("/driver/pickup/accept-order/{order_id}")
def accept_order_by_driver_for_pickup(order_id: int = Path(..., title="Id of order being accepted"), driver_id: int = Depends(auth_service.verify_jwt_token_driver), db: Session = Depends(get_db)):
    db_order = order_service.get_order_by_id(db, order_id)
    if not db_order:
        raise HTTPException(status_code=400, detail="Invalid Order Id.")

    db_order.order_status = OrderStatus.DRIVER_ACCEPTED_FOR_PICKUP
    db_order.pickup_driver_id = driver_id
    db.commit()
    return db_order


@app.put("/driver/dropoff/accept-order/{order_id}")
def accept_order_by_driver_for_dropoff(order_id: int = Path(..., title="Id of order being accepted"), driver_id: int = Depends(auth_service.verify_jwt_token_driver), db: Session = Depends(get_db)):
    db_order = order_service.get_order_by_id(db, order_id)
    if not db_order:
        raise HTTPException(status_code=400, detail="Invalid Order Id.")

    db_order.order_status = OrderStatus.DRIVER_ACCEPTED_FOR_DROPOFF
    db_order.dropoff_driver_id = driver_id
    db.commit()
    return db_order


@app.get("/driver/order/")
def get_driver_orders_by_order_status_in(order_status: List[OrderStatus] = Query([], title="Order status"), driver_id: int = Depends(auth_service.verify_jwt_token_driver), db: Session = Depends(get_db)):
    return driver_service.get_driver_orders_by_order_status_in(db, driver_id, order_status)


@app.get("/laundromart/order")
def get_laundromart_orders_by_order_status_in(order_status: List[OrderStatus] = Query([], title="Order status"), laundromart_id: int = Depends(auth_service.verify_jwt_token_laundromart), db: Session = Depends(get_db)):
    return laundromart_service.get_laundromart_orders_by_order_status_in(db, laundromart_id, order_status)


@app.put("/order/{order_id}")
def update_order(order_update: Optional[schemas.OrderUpdate], order_id: int, customer_id: int = Depends(auth_service.verify_jwt_token_update_order), db: Session = Depends(get_db)):
    return order_service.update_order(db, order_id, order_update)


@app.post("/customer/address/", response_model=schemas.CustomerAddress)
def create_customer_address(address_create: schemas.CustomerAddressCreate, customer_id: int = Depends(auth_service.verify_jwt_token_customer), db: Session = Depends(get_db)):
    return address_service.create_customer_address(db, customer_id, address_create)


@app.get("/customer/address/{address_id}", response_model=schemas.CustomerAddress)
def get_customer_address(address_id: int, customer_id: int = Depends(auth_service.verify_jwt_token_customer), db: Session = Depends(get_db)):
    return address_service.get_customer_address_by_id(db, address_id)


@app.get("/customer/address/", response_model=List[schemas.CustomerAddress])
def get_customer_address_list(customer_id: int = Depends(auth_service.verify_jwt_token_customer), db: Session = Depends(get_db)):
    return address_service.get_customer_address_list(db, customer_id)


@app.put("/customer/address/{address_id}", response_model=List[schemas.CustomerAddressUpdate])
def update_customer_address(address_id: int, customer_address_update: schemas.CustomerAddressUpdate, customer_id: int = Depends(auth_service.verify_jwt_token_customer), db: Session = Depends(get_db)):
    return address_service.update_customer_address_by_id(db, address_id, customer_address_update)


@app.put("/customer/default-address", response_model=schemas.Customer)
def update_customer_default_address(default_address_update: schemas.DefaultAddressUpdate, customer_id: int = Depends(auth_service.verify_jwt_token_customer), db: Session = Depends(get_db)):
    return address_service.update_customer_default_address(db, customer_id, default_address_update)


@app.put("/order/{order_id}/image/")
def upload_order_images(images: List[UploadFile], order_id: int, driver_id: int = Depends(auth_service.verify_jwt_token_driver), db: Session = Depends(get_db)):
    return order_service.upload_order_images(db, order_id, images)


@app.put("/driver/location/", response_model=schemas.Driver)
def update_driver_location(driver_location: schemas.DriverLocation, driver_id: int = Depends(auth_service.verify_jwt_token_driver), db: Session = Depends(get_db)):
    return driver_service.update_driver_location(db, driver_id, driver_location)


@app.get("/driver/location/", response_model=schemas.Driver)
def get_driver_location(driver_id: int = Depends(auth_service.verify_jwt_token_driver), db: Session = Depends(get_db)):
    return driver_service.get_driver_location(db, driver_id)


@app.put("/order/{order_id}/fulfillment/", response_model=schemas.Order)
def begin_order_fulfillment(order_id: int, order_fulfillment: schemas.OrderFulfillment, laundromart_id: int = Depends(auth_service.verify_jwt_token_laundromart), db: Session = Depends(get_db)):
    return order_service.begin_fulfillment(db, order_id, order_fulfillment)


@app.post("/register-device", response_model=schemas.DeviceToken)
def register_device_for_notification(customer_device_registration: schemas.CustomerDeviceRegistration, user_id:  int = Depends(auth_service.verify_jwt_token_register_device), db: Session = Depends(get_db)):
    return firebase_service.register_device_for_notification(db, customer_device_registration=customer_device_registration)


@app.post("/customer/notification/")
def test_customer_notification(test_customer_notification: schemas.TestCustomerNotification, db: Session = Depends(get_db)):
    return firebase_service.send_push_notification_to_customer(db, test_customer_notification.customer_id, test_customer_notification.notification_data)


@app.get("/verify-jwt-token/")
def verify_jwt_token(Authorization: str = Header(..., convert_underscores=False)):
    return auth_service.decode_token(Authorization)
