from sqlalchemy.orm import Session
import models
import schemas
from passlib.context import CryptContext


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = password_context.hash(user.password)
    user_model = models.User(first_name=user.first_name, last_name=user.last_name, email=user.email,
                             phone_no=user.phone_no, is_active=True, is_verified=False, password=hashed_password)
    db.add(user_model)
    db.commit()
    return user_model


def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def update_user_details(db: Session, user_id: int, updated_user: schemas.UserUpdate):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    for field in schemas.UserUpdate.__annotations__.keys():
        field_value = getattr(updated_user, field)
        if field_value:
            setattr(db_user, field, field_value)
    db.commit()
    return db_user


def create_user_address(db: Session, user_id: int, address_create: schemas.AddressCreate):
    address_model = models.CustomerAddress(full_address=address_create.full_address, landmark=address_create.landmark, buzzer_code=address_create.buzzer_code,
                                           delivery_door=address_create.delivery_door, latitude=address_create.latitude, longitude=address_create.longitude, address_type=address_create.address_type, user_id=user_id)
    db.add(address_model)
    db.commit()
    return address_model


def get_user_address_list(db: Session, user_id: int):
    return db.query(models.CustomerAddress).filter(models.CustomerAddress.user_id == user_id).all()
