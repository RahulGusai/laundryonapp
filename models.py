from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, JSON, DateTime, UniqueConstraint, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Customer(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(length=50))
    last_name = Column(String(length=50))
    email = Column(String(length=50), unique=True, index=True)
    phone_no = Column(String(length=50), unique=True, index=True)
    password = Column(String(length=255))
    is_active = Column(Boolean)
    is_verified = Column(Boolean)
    default_address_id = Column(Integer)
    address_list = relationship("CustomerAddress", back_populates="customer")
    orders = relationship("Order", back_populates="customer")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True),
                        server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, default=None)


class CustomerAddress(Base):
    __tablename__ = 'customer_address'
    id = Column(Integer, primary_key=True, index=True)
    full_address = Column(String(length=255))
    landmark = Column(String(length=100))
    buzzer_code = Column(String(length=50))
    delivery_door = Column(String(length=50))
    latitude = Column(Float)
    longitude = Column(Float)
    address_type = Column(String(length=50))
    customer_id = Column(Integer, ForeignKey('customers.id'))
    customer = relationship("Customer", back_populates="address_list")

    def to_dict(self):
        return {
            "full_address": self.full_address,
            "landmark": self.landmark,
            "buzzer_code": self.buzzer_code,
            "delivery_door": self.delivery_door,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "address_type": self.address_type
        }


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(length=50))
    details = Column(JSON)
    pickup_time = Column(DateTime)
    dropoff_time = Column(DateTime)
    payment_status = Column(String(length=50))
    order_status = Column(String(length=50))
    customer_id = Column(Integer, ForeignKey('customers.id'))
    customer = relationship("Customer", back_populates="orders")
    pickup_driver_id = Column(Integer, ForeignKey('drivers.id'))
    pickup_driver = relationship("Driver", foreign_keys=[
                                 pickup_driver_id], back_populates="pickup_orders")
    dropoff_driver_id = Column(Integer, ForeignKey('drivers.id'))
    dropoff_driver = relationship("Driver", foreign_keys=[
                                  dropoff_driver_id], back_populates="dropoff_orders")
    laundromart_id = Column(Integer, ForeignKey('laundromarts.id'))
    laundromart = relationship("LaundroMart", back_populates="orders")
    customer_address = Column(JSON)
    laundromart_address = Column(JSON)
    order_payment = relationship("OrderPayment",
                                 uselist=False, back_populates="order")
    order_meta = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True),
                        server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, default=None)


class OrderPayment(Base):
    __tablename__ = "order_payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_intent = Column(JSON)
    order_id = Column(Integer, ForeignKey(
        'orders.id'), unique=True)
    order = relationship(
        "Order", back_populates="order_payment")


class Driver(Base):
    __tablename__ = 'drivers'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(length=50))
    last_name = Column(String(length=50))
    email = Column(String(length=50), unique=True, index=True)
    phone_no = Column(String(length=50), unique=True, index=True)
    address = Column(JSON)
    password = Column(String(length=255))
    documents = Column(JSON)
    is_phone_verified = Column(Boolean)
    is_background_verified = Column(Boolean)
    is_active = Column(Boolean)
    pickup_orders = relationship("Order", foreign_keys=[
                                 Order.pickup_driver_id], back_populates="pickup_driver")
    dropoff_orders = relationship(
        "Order", foreign_keys=[Order.dropoff_driver_id], back_populates="dropoff_driver")
    driver_location = relationship("DriverLocation",
                                   uselist=False, back_populates="driver")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True),
                        server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, default=None)


class DriverLocation(Base):
    __tablename__ = 'driver_location'

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey('drivers.id'), unique=True)
    driver = relationship(
        "Driver", back_populates="driver_location")
    latitude = Column(Float)
    longitude = Column(Float)


class LaundroMart(Base):
    __tablename__ = 'laundromarts'

    id = Column(Integer, primary_key=True, index=True)
    laundromart_name = Column(String(length=50))
    email = Column(String(length=50), unique=True, index=True)
    phone_no = Column(String(length=50), unique=True, index=True)
    password = Column(String(length=255))
    is_phone_verified = Column(Boolean)
    is_active = Column(Boolean)
    address = relationship("LaundromartAddress",
                           uselist=False, back_populates="laundromart")
    orders = relationship("Order", back_populates="laundromart")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True),
                        server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, default=None)


class LaundromartAddress(Base):
    __tablename__ = 'laundromart_address'
    id = Column(Integer, primary_key=True, index=True)
    full_address = Column(String(length=255))
    landmark = Column(String(length=100))
    latitude = Column(Float)
    longitude = Column(Float)
    address_type = Column(String(length=50))
    laundromart_id = Column(Integer, ForeignKey(
        'laundromarts.id'), unique=True)
    laundromart = relationship(
        "LaundroMart", back_populates="address")


class DeviceTokens(Base):
    __tablename__ = 'device_tokens'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    user_role = Column(String(length=50))
    token = Column(String(length=500))

    __table_args__ = (
        UniqueConstraint('user_id', 'user_role',
                         name='unique_user_id_role_combination'),
    )
