from typing import List
from sqlalchemy.orm import Session
from enums import OrderStatus
import models
import schemas
from passlib.context import CryptContext

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_laundromart_by_id(db: Session, laundromart_id: int):
    return db.query(models.LaundroMart).filter(models.LaundroMart.id == laundromart_id).first()


def get_laundromart_by_email(db: Session, email: str):
    return db.query(models.LaundroMart).filter(models.LaundroMart.email == email).first()


def create_laundromart(db: Session, laundromart: schemas.LaundroMartCreate):
    hashed_password = password_context.hash(laundromart.password)
    laundromart_model = models.LaundroMart(laundromart_name=laundromart.laundromart_name, email=laundromart.email, phone_no=laundromart.phone_no,
                                           password=hashed_password, is_active=True, is_phone_verified=True)
    db.add(laundromart_model)
    db.commit()

    laundromart_address_schema = laundromart.address
    laundromart_address_model = models.LaundromartAddress(laundromart_id=laundromart_model.id, full_address=laundromart_address_schema.full_address, landmark=laundromart_address_schema.landmark,
                                                          latitude=laundromart_address_schema.latitude, longitude=laundromart_address_schema.longitude, address_type=laundromart_address_schema.address_type)
    db.add(laundromart_address_model)
    db.commit()

    return laundromart_model


def get_laundromart_orders_by_order_status_in(db: Session, laundromart_id: int, order_status_list: List[OrderStatus]):
    query = db.query(models.Order).filter(
        models.Order.laundromart_id == laundromart_id)

    if order_status_list:
        query = query.filter(models.Order.order_status.in_(order_status_list))

    orders = query.all()
    return orders
