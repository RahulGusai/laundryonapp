from fastapi import HTTPException
from sqlalchemy.orm import Session
import models
import schemas


def validate_customer_registration(db: Session, customer: schemas.CustomerCreate):
    db_customer = db.query(models.Customer).filter(
        models.Customer.email == customer.email).first()
    if db_customer:
        raise HTTPException(
            status_code=400, detail="Email id is already registered.")

    db_customer = db.query(models.Customer).filter(
        models.Customer.phone_no == customer.phone_no).first()
    if db_customer:
        raise HTTPException(
            status_code=400, detail="Phone no is already registered.")


def validate_driver_registration(db: Session, driver: schemas.DriverCreate):
    db_driver = db.query(models.Driver).filter(
        models.Driver.email == driver.email).first()
    if db_driver:
        raise HTTPException(
            status_code=400, detail="Email id is already registered.")

    db_driver = db.query(models.Driver).filter(
        models.Driver.phone_no == driver.phone_no).first()
    if db_driver:
        raise HTTPException(
            status_code=400, detail="Phone no is already registered.")


def validate_laundromart_registration(db: Session, laundromart: schemas.LaundroMartCreate):
    db_laundromart = db.query(models.LaundroMart).filter(
        models.LaundroMart.email == laundromart.email).first()
    if db_laundromart:
        raise HTTPException(
            status_code=400, detail="Email id is already registered.")

    db_laundromart = db.query(models.LaundroMart).filter(
        models.LaundroMart.phone_no == laundromart.phone_no).first()
    if db_laundromart:
        raise HTTPException(
            status_code=400, detail="Phone no is already registered.")
