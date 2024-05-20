from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session
import customer_service

import models
import schemas


def get_customer_address_by_id(db: Session, address_id: int):
    return db.query(models.CustomerAddress).filter(models.CustomerAddress.id == address_id).first()


def update_customer_address_by_id(db: Session, address_id: int, customer_address_update: schemas.CustomerAddressUpdate):
    db_address = db.query(models.CustomerAddress).filter(
        models.CustomerAddress.id == address_id).first()

    for field in schemas.CustomerAddressUpdate.__annotations__.keys():
        field_value = getattr(customer_address_update, field)
        if field_value:
            setattr(db_address, field, field_value)
    db.commit()
    return db_address


def create_customer_address(db: Session, customer_id: int, address_create: schemas.CustomerAddressCreate):
    address_model = models.CustomerAddress(full_address=address_create.full_address, landmark=address_create.landmark, buzzer_code=address_create.buzzer_code,
                                           delivery_door=address_create.delivery_door, latitude=address_create.latitude, longitude=address_create.longitude, address_type=address_create.address_type, customer_id=customer_id)

    db.add(address_model)
    db.commit()

    db_customer = customer_service.get_customer_by_id(db, customer_id)
    if db_customer.default_address_id == None:
        db_customer.default_address_id = address_model.id
    db.commit()

    return address_model


def get_customer_address_list(db: Session, customer_id: int):
    return db.query(models.CustomerAddress).filter(models.CustomerAddress.customer_id == customer_id).all()


def update_customer_default_address(db: Session, customer_id: int, default_address_update: schemas.DefaultAddressUpdate):
    db_address = db.query(models.CustomerAddress).filter(
        and_(models.CustomerAddress.id == default_address_update.address_id, models.CustomerAddress.customer_id == customer_id)).first()

    if not db_address:
        return HTTPException(status_code=400, detail="Invalid address Id.")

    db_customer = db.query(models.Customer).filter(
        models.Customer.id == customer_id).first()
    db_customer.default_address_id = default_address_update.address_id
    db.commit()

    return db_customer
