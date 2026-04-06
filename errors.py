from __future__ import annotations
from typing import Any, Callable


class AppError(Exception):
    def __init__(self, message: str, code: str = "UNKNOWN", context: dict | None = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}

    def to_dict(self) -> dict:
        return {"error": str(self), "code": self.code, "context": self.context}


class ValidationError(AppError):
    def __init__(self, field: str, reason: str):
        super().__init__(f"Validation failed for '{field}': {reason}", code="VALIDATION_ERROR",
                         context={"field": field, "reason": reason})


class NotFoundError(AppError):
    def __init__(self, resource: str, identifier: Any):
        super().__init__(f"{resource} '{identifier}' not found", code="NOT_FOUND",
                         context={"resource": resource, "id": identifier})


class AuthError(AppError):
    def __init__(self, reason: str = "Unauthorized"):
        super().__init__(reason, code="AUTH_ERROR")


class StockError(AppError):
    def __init__(self, product_id: int, requested: int, available: int):
        super().__init__(
            f"Insufficient stock for product {product_id}: requested {requested}, available {available}",
            code="STOCK_ERROR",
            context={"product_id": product_id, "requested": requested, "available": available},
        )


def wrap_error(exc: Exception, context: str = "") -> dict:
    if isinstance(exc, AppError):
        d = exc.to_dict()
    else:
        d = {"error": str(exc), "code": type(exc).__name__, "context": {}}
    if context:
        d["context"]["where"] = context
    return d


def safe_call(fn: Callable, *args, **kwargs) -> dict:
    try:
        result = fn(*args, **kwargs)
        return {"ok": True, "result": result}
    except Exception as exc:
        return {"ok": False, **wrap_error(exc, context=fn.__name__)}
