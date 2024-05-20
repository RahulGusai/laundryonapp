from datetime import timedelta, timezone
import datetime
from functools import partial
from fastapi import HTTPException, Header
import jwt
from enums import Roles

# Secret key to sign the JWT token (you should keep this secret)
SECRET_KEY = "private-key"
ALGORITHM = "HS256"


roles_dict = {"update_order": [Roles.DRIVER, Roles.LAUNDROMART],
              "get_orders_by_status_in": [Roles.DRIVER, Roles.LAUNDROMART], "register_device_for_notification": [Roles.CUSTOMER, Roles.LAUNDROMART, Roles.DRIVER]}


def generate_jwt_token(payload: dict, expires_delta: timedelta):
    to_encode = payload.copy()
    expire = datetime.datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    jwt_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return jwt_token


def decode_token(jwt_token: str):
    token_prefix, token = jwt_token.split(" ")

    if token_prefix.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=401, detail="Access token not provided.")

    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM])
        if ("id" not in payload) or ("role" not in payload):
            raise HTTPException(status_code=401, detail="Invalid access token")

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Access token is expired.")
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Invalid access token.")

    return payload


def verify_jwt_token_customer(Authorization: str = Header(..., convert_underscores=False)):
    jwt_token_payload = decode_token(Authorization)

    if (jwt_token_payload["id"] is None) or (jwt_token_payload["role"] != Roles.CUSTOMER):
        raise HTTPException(
            status_code=401, detail="Invalid access token.")
    return jwt_token_payload["id"]


def verify_jwt_token_driver(Authorization: str = Header(..., convert_underscores=False)):
    jwt_token_payload = decode_token(Authorization)

    if (jwt_token_payload["id"] is None) or (jwt_token_payload["role"] != Roles.DRIVER):
        raise HTTPException(
            status_code=401, detail="Invalid access token.")
    return jwt_token_payload["id"]


def verify_jwt_token_laundromart(Authorization: str = Header(..., convert_underscores=False)):
    jwt_token_payload = decode_token(Authorization)

    if (jwt_token_payload["id"] is None) or (jwt_token_payload["role"] != Roles.LAUNDROMART):
        raise HTTPException(
            status_code=401, detail="Invalid access token.")
    return jwt_token_payload["id"]


def verify_jwt_token_per_method_name(method_name: str):
    def verify_jwt_token(Authorization: str = Header(..., convert_underscores=False)):
        jwt_token_payload = decode_token(Authorization)
        if (jwt_token_payload["id"] is None) or (not (jwt_token_payload["role"] in roles_dict.get(method_name))):
            raise HTTPException(
                status_code=401, detail="Invalid access token.")

        return jwt_token_payload["id"]
    return verify_jwt_token


verify_jwt_token_update_order = partial(
    verify_jwt_token_per_method_name, "update_order")
verify_jwt_token_get_orders = partial(
    verify_jwt_token_per_method_name, "get_orders_by_status_in")
verify_jwt_token_register_device = partial(
    verify_jwt_token_per_method_name, "register_device_for_notification")
