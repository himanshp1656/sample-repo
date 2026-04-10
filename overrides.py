"""
overrides.py — Method overriding at multiple inheritance levels.

Shows how child classes override parent methods, call super(),
and how Python's MRO determines which version is called.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


# ── Basic override ────────────────────────────────────────────────────────────

class Formatter:
    def format(self, value: Any) -> str:
        return str(value)

    def format_many(self, values: List[Any]) -> List[str]:
        return [self.format(v) for v in values]   # calls self.format → polymorphic


class UpperFormatter(Formatter):
    def format(self, value: Any) -> str:           # override
        return str(value).upper()


class PrefixFormatter(Formatter):
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    def format(self, value: Any) -> str:           # override
        return f"{self.prefix}{value}"


class PrefixUpperFormatter(PrefixFormatter):
    def format(self, value: Any) -> str:           # override again
        return super().format(value).upper()       # calls PrefixFormatter.format then upper


# ── Override with super() chain ───────────────────────────────────────────────

class BaseHandler:
    def handle(self, request: Dict) -> Dict:
        return {"status": "ok", "source": "BaseHandler"}

    def validate(self, request: Dict) -> bool:
        return "action" in request


class AuthHandler(BaseHandler):
    def handle(self, request: Dict) -> Dict:       # override
        if not self.validate(request):
            return {"status": "error", "reason": "invalid"}
        result = super().handle(request)           # delegate to base
        result["auth"] = True
        return result

    def validate(self, request: Dict) -> bool:     # override
        return super().validate(request) and "token" in request


class LoggingHandler(AuthHandler):
    def handle(self, request: Dict) -> Dict:       # override
        print(f"→ {request}")
        result = super().handle(request)           # calls AuthHandler.handle
        print(f"← {result}")
        return result


class CachingHandler(LoggingHandler):
    def __init__(self) -> None:
        self._cache: Dict[str, Dict] = {}

    def handle(self, request: Dict) -> Dict:       # override
        key = str(sorted(request.items()))
        if key in self._cache:
            return {**self._cache[key], "cached": True}
        result = super().handle(request)           # calls LoggingHandler.handle
        self._cache[key] = result
        return result


# ── __dunder__ overrides ──────────────────────────────────────────────────────

class Money:
    def __init__(self, amount: float, currency: str = "USD") -> None:
        self.amount = round(amount, 2)
        self.currency = currency

    def __add__(self, other: "Money") -> "Money":
        self._check_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        self._check_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: float) -> "Money":
        return Money(self.amount * factor, self.currency)

    def __truediv__(self, divisor: float) -> "Money":
        return Money(self.amount / divisor, self.currency)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other: "Money") -> bool:
        self._check_currency(other)
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        return self == other or self < other

    def __repr__(self) -> str:
        return f"Money({self.amount}, {self.currency!r})"

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:.2f}"

    def __hash__(self) -> int:
        return hash((self.amount, self.currency))

    def _check_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise ValueError(f"Currency mismatch: {self.currency} vs {other.currency}")


class DiscountedMoney(Money):
    def __init__(self, amount: float, currency: str = "USD", discount: float = 0.0) -> None:
        super().__init__(amount * (1 - discount), currency)
        self.original = amount
        self.discount = discount

    def __repr__(self) -> str:                     # override
        return f"DiscountedMoney({self.original}, {self.currency!r}, discount={self.discount})"


# ── Property override ─────────────────────────────────────────────────────────

class Config:
    def __init__(self) -> None:
        self._debug = False

    @property
    def debug(self) -> bool:
        return self._debug

    @debug.setter
    def debug(self, value: bool) -> None:
        self._debug = bool(value)

    def get_settings(self) -> Dict:
        return {"debug": self.debug}


class VerboseConfig(Config):
    @property
    def debug(self) -> bool:                       # override getter
        print("Reading debug flag")
        return super().debug

    @debug.setter
    def debug(self, value: bool) -> None:          # override setter
        print(f"Setting debug to {value}")
        super(VerboseConfig, type(self)).debug.fset(self, value)  # type: ignore[attr-defined]


# ── Abstract override ─────────────────────────────────────────────────────────

from abc import ABC, abstractmethod


class Plugin(ABC):
    @abstractmethod
    def activate(self) -> None: ...

    @abstractmethod
    def deactivate(self) -> None: ...

    def reload(self) -> None:
        self.deactivate()
        self.activate()


class DatabasePlugin(Plugin):
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self._conn = None

    def activate(self) -> None:                    # override abstract
        print(f"Connecting to {self.dsn}")
        self._conn = object()   # placeholder

    def deactivate(self) -> None:                  # override abstract
        print("Closing connection")
        self._conn = None

    def query(self, sql: str) -> List[Dict]:
        if self._conn is None:
            raise RuntimeError("Not activated")
        return []


class CachedDatabasePlugin(DatabasePlugin):
    def __init__(self, dsn: str) -> None:
        super().__init__(dsn)
        self._cache: Dict[str, List] = {}

    def activate(self) -> None:                    # override concrete
        super().activate()
        self._cache.clear()

    def query(self, sql: str) -> List[Dict]:       # override concrete
        if sql not in self._cache:
            self._cache[sql] = super().query(sql)
        return self._cache[sql]
