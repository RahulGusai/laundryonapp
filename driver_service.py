from typing import List
from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from enums import OrderStatus
import models
import laundromart_service
import schemas

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_driver_by_email(db: Session, email: str):
    return db.query(models.Driver).filter(models.Driver.email == email).first()


def create_driver(db: Session, driver: schemas.DriverCreate):
    hashed_password = password_context.hash(driver.password)
    driver_model = models.Driver(first_name=driver.first_name, last_name=driver.last_name, email=driver.email,
                                 phone_no=driver.phone_no, is_active=True, is_phone_verified=False, is_background_verified=False, password=hashed_password, documents={})
    db.add(driver_model)

    if driver.is_laundromart:
        if not driver.address:
            raise HTTPException(
                status_code=400, detail="Address is mandatory if signing up for laundromart as well.")
        laundromart_create_schema = schemas.LaundroMartCreate(
            laundromart_name=driver.first_name, email=driver.email, phone_no=driver.phone_no, address=driver.address, password=driver.password)
        laundromart_service.create_laundromart(db, laundromart_create_schema)

    db.commit()
    return driver_model


def get_driver_by_id(db: Session, driver_id: int):
    return db.query(models.Driver).filter(models.Driver.id == driver_id).first()


def get_driver_orders_by_order_status_in(db: Session, driver_id: int, order_status_list: List[OrderStatus]):
    query = db.query(models.Order).filter(or_(models.Order.pickup_driver_id ==
                                          driver_id, models.Order.dropoff_driver_id == driver_id))

    if order_status_list:
        query = query.filter(models.Order.order_status.in_(order_status_list))

    orders = query.all()
    return orders


def get_driver_location(db: Session, driver_id: int):
    return db.query(models.Driver).filter(models.Driver.id == driver_id).first()


def update_driver_location(db: Session, driver_id: int, driver_location: schemas.DriverLocation):
    db_driver_location = db.query(models.Driver).filter(
        models.Driver.id == driver_id).first()

    if not db_driver_location:
        db_driver_location = models.DriverLocation(
            latitude=db_driver_location.latitude, longitude=db_driver_location.longitude)
        db.add(db_driver_location)
        db.commit()
        return db_driver_location

    db_driver_location.latitude = driver_location.latitude
    db_driver_location.longitude = driver_location.longitude
    db.commit()
    return db_driver_location
