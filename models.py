from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import time


@dataclass
class Product:
    id: int
    name: str
    price: float
    stock: int
    category: str = "general"
    tags: List[str] = field(default_factory=list)

    def is_available(self) -> bool:
        return self.stock > 0

    def discounted_price(self, pct: float) -> float:
        if not (0 <= pct <= 100):
            raise ValueError(f"Discount must be 0-100, got {pct}")
        return round(self.price * (1 - pct / 100), 2)


@dataclass
class User:
    id: int
    username: str
    email: str
    role: str = "user"
    is_active: bool = True
    metadata: dict = field(default_factory=dict)

    def display_name(self) -> str:
        return self.metadata.get("display_name") or self.username

    def has_role(self, role: str) -> bool:
        return self.role == role


@dataclass
class OrderItem:
    product_id: int
    quantity: int
    unit_price: float

    def subtotal(self) -> float:
        return round(self.quantity * self.unit_price, 2)


@dataclass
class Order:
    id: str
    user_id: int
    items: List[OrderItem] = field(default_factory=list)
    status: str = "pending"
    created_at: float = field(default_factory=time.time)
    discount_pct: float = 0.0

    def gross_total(self) -> float:
        return round(sum(item.subtotal() for item in self.items), 2)

    def net_total(self) -> float:
        gross = self.gross_total()
        return round(gross * (1 - self.discount_pct / 100), 2)

    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)
