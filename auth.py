from __future__ import annotations
import hashlib
import hmac
import time
import json
import base64
from typing import Optional
from errors import AuthError, NotFoundError
from validators import validate_password, validate_email

SECRET_KEY = "super-secret-key-change-in-prod"
TOKEN_TTL = 3600  # seconds

# In-memory token store (simulating Redis)
_active_tokens: dict[str, dict] = {}
_revoked_tokens: set[str] = set()


def hash_password(password: str) -> str:
    validate_password(password)
    salt = "static-salt-for-demo"
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_password(password), hashed)


def generate_token(user_id: int, role: str, extra: dict | None = None) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + TOKEN_TTL,
        **(extra or {}),
    }
    raw = json.dumps(payload, separators=(",", ":"))
    token = base64.b64encode(raw.encode()).decode()
    sig = hmac.new(SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()
    full_token = f"{token}.{sig}"
    _active_tokens[full_token] = payload
    return full_token


def decode_token(token: str) -> dict:
    if token in _revoked_tokens:
        raise AuthError("Token has been revoked")
    try:
        parts = token.split(".")
        if len(parts) != 2:
            raise AuthError("Malformed token")
        encoded, sig = parts
        expected_sig = hmac.new(SECRET_KEY.encode(), encoded.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            raise AuthError("Invalid token signature")
        payload = json.loads(base64.b64decode(encoded.encode()).decode())
    except AuthError:
        raise
    except Exception:
        raise AuthError("Could not decode token")
    if payload.get("exp", 0) < time.time():
        raise AuthError("Token has expired")
    return payload


def check_permission(token: str, required_role: str) -> bool:
    payload = decode_token(token)
    user_role = payload.get("role", "")
    role_hierarchy = {"admin": 3, "moderator": 2, "user": 1, "guest": 0}
    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    if user_level < required_level:
        raise AuthError(f"Role '{user_role}' cannot perform action requiring '{required_role}'")
    return True


def revoke_token(token: str) -> bool:
    if token in _active_tokens:
        del _active_tokens[token]
    _revoked_tokens.add(token)
    return True


class AuthService:
    def __init__(self, user_store: dict | None = None):
        # user_store: {username: {id, hashed_password, role, email}}
        self._users: dict[str, dict] = user_store or {}

    def register(self, username: str, password: str, email: str, role: str = "user") -> dict:
        validate_email(email)
        if username in self._users:
            raise AuthError(f"Username '{username}' already exists")
        hashed = hash_password(password)
        user = {"id": len(self._users) + 1, "username": username,
                "email": email, "hashed_password": hashed, "role": role}
        self._users[username] = user
        return {"id": user["id"], "username": username, "email": email, "role": role}

    def login(self, username: str, password: str) -> dict:
        user = self._users.get(username)
        if not user:
            raise NotFoundError("User", username)
        if not verify_password(password, user["hashed_password"]):
            raise AuthError("Invalid password")
        token = generate_token(user["id"], user["role"], extra={"username": username})
        return {"token": token, "user_id": user["id"], "role": user["role"]}

    def logout(self, token: str) -> bool:
        revoke_token(token)
        return True

    def refresh_token(self, token: str) -> str:
        payload = decode_token(token)
        revoke_token(token)
        return generate_token(payload["sub"], payload["role"])

    def get_user_from_token(self, token: str) -> dict:
        payload = decode_token(token)
        username = payload.get("username")
        if not username or username not in self._users:
            raise NotFoundError("User", payload.get("sub"))
        user = self._users[username]
        return {"id": user["id"], "username": username, "email": user["email"], "role": user["role"]}
