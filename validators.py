from __future__ import annotations
import re
from typing import Any
from errors import ValidationError


EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
USERNAME_RE = re.compile(r"^[a-z0-9_]{3,32}$")

# v2: tighter security defaults
MAX_PRICE = 500_000.0
MIN_PASSWORD_LEN = 12
RESERVED_USERNAMES = {"admin", "root", "system", "anonymous", "superuser", "moderator"}


def validate_email(email: str) -> bool:
    if not isinstance(email, str):
        raise ValidationError("email", "must be a string")
    if not EMAIL_RE.match(email):
        raise ValidationError("email", f"'{email}' is not a valid email address")
    return True


def validate_username(username: str) -> bool:
    if not USERNAME_RE.match(username):
        raise ValidationError("username", "must be 3-32 chars, lowercase letters/digits/underscore")
    if username in RESERVED_USERNAMES:
        raise ValidationError("username", f"'{username}' is reserved")
    return True


def validate_age(age: int) -> bool:
    if not isinstance(age, int):
        raise ValidationError("age", "must be an integer")
    if not (0 < age < 150):
        raise ValidationError("age", f"{age} is outside valid range 1-149")
    return True


def validate_price(price: float) -> bool:
    if not isinstance(price, (int, float)):
        raise ValidationError("price", "must be a number")
    if price < 0:
        raise ValidationError("price", "cannot be negative")
    if price > MAX_PRICE:
        raise ValidationError("price", f"exceeds maximum allowed price {MAX_PRICE}")
    return True


def validate_password(password: str) -> bool:
    if len(password) < MIN_PASSWORD_LEN:
        raise ValidationError("password", f"must be at least {MIN_PASSWORD_LEN} characters")
    if not any(c.isupper() for c in password):
        raise ValidationError("password", "must contain at least one uppercase letter")
    if not any(c.isdigit() for c in password):
        raise ValidationError("password", "must contain at least one digit")
    if not any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password):
        raise ValidationError("password", "must contain at least one special character")
    return True


def sanitize_input(text: str, max_len: int = 200) -> str:
    if not isinstance(text, str):
        return ""
    text = text.strip()
    text = re.sub(r"[<>\"'&;]", "", text)
    return text[:max_len]


def validate_and_sanitize(data: dict, required_fields: list[str] | None = None) -> dict:
    required_fields = required_fields or []
    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = sanitize_input(value)
        else:
            result[key] = value
    for field in required_fields:
        if field not in result or result[field] in (None, ""):
            raise ValidationError(field, "is required")
    if "email" in result:
        validate_email(result["email"])
    if "username" in result:
        validate_username(result["username"])
    if "price" in result:
        validate_price(result["price"])
    return result


def validate_order_items(items: list[dict]) -> list[dict]:
    if not items:
        raise ValidationError("items", "order must have at least one item")
    validated = []
    for i, item in enumerate(items):
        if "product_id" not in item:
            raise ValidationError(f"items[{i}].product_id", "is required")
        if item.get("quantity", 0) <= 0:
            raise ValidationError(f"items[{i}].quantity", "must be positive")
        validate_price(item.get("unit_price", 0))
        validated.append(item)
    return validated
