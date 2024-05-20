from datetime import datetime
from typing import List, Optional
from fastapi import UploadFile
from pydantic import BaseModel

from enums import OrderCategory, OrderStatus, PaymentStatus, Roles


class CustomerBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_no: str


class CustomerCreate(CustomerBase):
    password: str


class CustomerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_no: Optional[str] = None


class CustomerAddressCreate(BaseModel):
    full_address: str
    landmark: str
    buzzer_code: str
    delivery_door: str
    latitude: float
    longitude: float
    address_type: str


class CustomerAddressUpdate(BaseModel):
    full_address: Optional[str]
    landmark: Optional[str]
    buzzer_code: Optional[str]
    delivery_door: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    address_type: Optional[str]


class CustomerAddress(CustomerAddressCreate):
    id: int

    class Config:
        from_attributes = True


class DefaultAddressUpdate(BaseModel,):
    address_id: int


class Customer(CustomerBase):
    id: int
    is_active: bool
    is_verified: bool
    default_address_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LaundroMartAddress(BaseModel):
    full_address: str
    landmark: str
    latitude: float
    longitude: float
    address_type: str


class DriverCreate(CustomerBase):
    password: str
    is_laundromart: bool
    address: Optional[LaundroMartAddress] = None


class Driver(CustomerBase):
    id: int
    is_active: bool
    is_phone_verified: bool
    is_background_verified: bool
    documents: dict
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DriverLocation(BaseModel):
    latitude: float
    longitude: float


class LaundroMartCreate(BaseModel):
    laundromart_name: str
    email: str
    phone_no: str
    address: LaundroMartAddress
    password: str


class LaundroMart(BaseModel):
    id: int
    laundromart_name: str
    email: str
    phone_no: str
    address: LaundroMartAddress
    is_active: bool
    is_phone_verified: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class Login(BaseModel):
    email: str
    password: str


class OrderDetails(BaseModel):
    weight: Optional[float] = None
    items: dict
    additional_requests: Optional[dict] = None
    special_instructions: Optional[List[str]] = None

    def to_dict(self):
        return {
            'weight': self.weight,
            'items': self.items,
            'additional_requests': self.additional_requests,
            'special_instructions': self.special_instructions
        }


class OrderCreate(BaseModel):
    category: OrderCategory
    details: OrderDetails
    customer_address_id: int
    pickup_time: datetime
    dropoff_time: datetime


class OrderUpdate(BaseModel):
    weight: Optional[float] = None
    order_status: Optional[OrderStatus] = None


class OrderPayment(BaseModel):
    payment_intent: dict


class Order(BaseModel):
    id: int
    category: OrderCategory
    details: OrderDetails
    pickup_time: datetime
    dropoff_time: datetime
    customer: Customer
    customer_address: dict
    laundromart_address: Optional[dict] = None
    pickup_driver_id: Optional[int] = None
    dropoff_driver_id: Optional[int] = None
    order_payment: Optional[OrderPayment] = None
    order_status: Optional[OrderStatus]
    order_meta: dict
    payment_status: PaymentStatus
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderFulfillment(BaseModel):
    amount_to_capture: float
    reason: Optional[str] = None


class CustomerDeviceRegistration(BaseModel):
    user_id: int
    user_role: Roles
    token: str


class DeviceToken(BaseModel):
    user_id: int
    user_role: Roles
    token: str


class TestCustomerNotification(BaseModel):
    customer_id: int
    notification_data: dict
