from enum import Enum


class OrderCategory(str, Enum):
    LAUNDRY = "Laundry"
    ONLY_IRON = "Only Iron"
    DRY_CLEAN = "Dry Clean"


class PaymentStatus(str, Enum):
    PAYMENT_INITIALIZED = "payment_initialized"
    PAYMENT_ON_HOLD = "payment_on_hold"
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_FAILED = "payment_failed"


class OrderStatus(str, Enum):
    ORDER_CREATED = "order_created"
    LAUNDROMART_ACCEPTED = "laundromart_accepted"
    DRIVER_ACCEPTED_FOR_PICKUP = "driver_accepted_for_pickup"
    PICKED_FROM_CUSTOMER = "picked_from_customer"
    AT_LAUNDROMART = "at_laundromart"
    ORDER_FULFILLMENT = 'order_fulfillment'
    READY_FOR_PICKUP = "ready_for_pickup"
    DRIVER_ACCEPTED_FOR_DROPOFF = "driver_acceped_for_dropoff"
    PICKED_FROM_LAUNDROMART = "picked_from_laundromart"
    ORDER_COMPLETED = "order_completed"
    ORDER_CANCELLED = "order_cancelled"


class Roles(str, Enum):
    CUSTOMER = "Customer"
    DRIVER = "Driver"
    LAUNDROMART = "LaundroMart"


class NotificationType(str, Enum):
    PAYMENT_INTENT_CREATED = "payment_intent_created"
