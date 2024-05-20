from fastapi import HTTPException
import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy import and_
import customer_service
from enums import Roles
import models
from sqlalchemy.orm import Session
from schemas import CustomerDeviceRegistration

cred = credentials.Certificate(
    "/etc/cred/firebase.json")
firebase_admin.initialize_app(cred)


def register_device_for_notification(db: Session, customer_device_registration: CustomerDeviceRegistration):
    validate_user_id(db, customer_device_registration.user_id,
                     customer_device_registration.user_role)

    db_device_token = db.query(models.DeviceTokens).filter(
        and_(models.DeviceTokens.user_id == customer_device_registration.user_id, models.DeviceTokens.user_role == customer_device_registration.user_role)).first()
    if not db_device_token:
        db_device_token = models.DeviceTokens(user_id=customer_device_registration.user_id,
                                              user_role=customer_device_registration.user_role, token=customer_device_registration.token)
        db.add(db_device_token)
        db.commit()
        return db_device_token

    db_device_token.token = customer_device_registration.token
    db.commit()
    return db_device_token


def validate_user_id(db: Session, user_id: int, user_role: Roles):
    if user_role == Roles.CUSTOMER:
        if not customer_service.get_customer_by_id(db, user_id):
            raise HTTPException(status_code=400, detail="Invalid Customer Id.")


def send_push_notification_to_customer(db: Session, customer_id: int, notification_data: dict):
    db_device_token = db.query(models.DeviceTokens).filter(and_(
        models.DeviceTokens.user_id == customer_id, models.DeviceTokens.user_role == Roles.CUSTOMER)).first()

    if not db_device_token:
        raise HTTPException(
            status_code=400, detail=f"No device token found for the customer id - {customer_id}.")

    message = messaging.Message(
        data=notification_data, token=db_device_token.token)
    response = messaging.send(message=message)
    print(f"Response from firebase server - {response}")
