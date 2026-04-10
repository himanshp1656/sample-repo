"""
dataclasses_demo.py — @dataclass, frozen dataclasses, __post_init__,
field(), ClassVar, and dataclass inheritance.
"""
from __future__ import annotations

from dataclasses import dataclass, field, InitVar, KW_ONLY, fields
from typing import ClassVar, List, Optional
import uuid


# ── Basic dataclass ───────────────────────────────────────────────────────────

@dataclass
class Point:
    x: float
    y: float

    def distance_to(self, other: "Point") -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def translate(self, dx: float, dy: float) -> "Point":
        return Point(self.x + dx, self.y + dy)


@dataclass
class Point3D(Point):
    z: float = 0.0

    def distance_to(self, other: "Point3D") -> float:          # override
        return (
            (self.x - other.x) ** 2
            + (self.y - other.y) ** 2
            + (self.z - other.z) ** 2
        ) ** 0.5


# ── Frozen (immutable) dataclass ──────────────────────────────────────────────

@dataclass(frozen=True)
class Currency:
    code: str
    symbol: str
    decimals: int = 2

    def format_amount(self, amount: float) -> str:
        return f"{self.symbol}{amount:.{self.decimals}f}"


# ── __post_init__ and InitVar ─────────────────────────────────────────────────

@dataclass
class HashedPassword:
    plain: InitVar[str]                            # consumed in __post_init__, not stored
    _hash: str = field(init=False, repr=False)

    def __post_init__(self, plain: str) -> None:
        import hashlib
        self._hash = hashlib.sha256(plain.encode()).hexdigest()

    def verify(self, plain: str) -> bool:
        import hashlib
        return self._hash == hashlib.sha256(plain.encode()).hexdigest()


# ── field() with defaults and metadata ───────────────────────────────────────

@dataclass
class Product:
    name: str
    price: float
    tags: List[str] = field(default_factory=list)
    sku: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    in_stock: bool = field(default=True, metadata={"db_column": "in_stock"})

    # ClassVar — not a field, shared across instances
    _registry: ClassVar[List["Product"]] = []

    def __post_init__(self) -> None:
        if self.price < 0:
            raise ValueError("price cannot be negative")
        Product._registry.append(self)

    @classmethod
    def all(cls) -> List["Product"]:
        return cls._registry[:]

    def apply_discount(self, pct: float) -> "Product":
        return Product(
            name=self.name,
            price=self.price * (1 - pct),
            tags=self.tags[:],
            in_stock=self.in_stock,
        )


# ── Dataclass inheritance ─────────────────────────────────────────────────────

@dataclass
class BaseEntity:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=__import__("time").time)


@dataclass
class User(BaseEntity):
    username: str = ""
    email: str = ""
    is_active: bool = True

    def deactivate(self) -> None:
        self.is_active = False


@dataclass
class AdminUser(User):
    permissions: List[str] = field(default_factory=list)

    def grant(self, perm: str) -> None:
        if perm not in self.permissions:
            self.permissions.append(perm)

    def revoke(self, perm: str) -> None:
        self.permissions = [p for p in self.permissions if p != perm]

    def has_permission(self, perm: str) -> bool:
        return perm in self.permissions


# ── __eq__ and __hash__ control ───────────────────────────────────────────────

@dataclass(eq=True, unsafe_hash=True)
class Tag:
    """Tags are compared and hashed by name only."""
    name: str
    color: str = "#000000"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Tag):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)


# ── Utility functions ─────────────────────────────────────────────────────────

def field_names(dc) -> List[str]:
    return [f.name for f in fields(dc)]


def clone(entity: BaseEntity, **overrides) -> BaseEntity:
    import dataclasses
    return dataclasses.replace(entity, **overrides)
