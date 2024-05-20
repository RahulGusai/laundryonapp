from sqlalchemy.orm import Session
import models
import schemas
from passlib.context import CryptContext


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_customer_by_email(db: Session, email: str):
    return db.query(models.Customer).filter(models.Customer.email == email).first()


def create_customer(db: Session, customer: schemas.CustomerCreate):
    hashed_password = password_context.hash(customer.password)
    customer_model = models.Customer(first_name=customer.first_name, last_name=customer.last_name, email=customer.email,
                                     phone_no=customer.phone_no, is_active=True, is_verified=False, password=hashed_password)
    db.add(customer_model)
    db.commit()
    return customer_model


def get_customer_by_id(db: Session, customer_id: int):
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()


def update_customer_details(db: Session, customer_id: int, updated_customer: schemas.CustomerUpdate):
    db_customer = db.query(models.Customer).filter(
        models.Customer.id == customer_id).first()
    for field in schemas.customerUpdate.__annotations__.keys():
        field_value = getattr(updated_customer, field)
        if field_value:
            setattr(db_customer, field, field_value)
    db.commit()
    return db_customer
