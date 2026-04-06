from __future__ import annotations
import uuid
import time
from typing import List, Optional
from models import Order, OrderItem, Product
from errors import StockError, NotFoundError, ValidationError
from validators import validate_order_items
from cache import get_cache, set_cache, invalidate

# Simulated product DB
_products: dict[int, Product] = {
    1: Product(id=1, name="Widget A", price=9.99,  stock=100, category="widgets"),
    2: Product(id=2, name="Widget B", price=24.99, stock=50,  category="widgets"),
    3: Product(id=3, name="Gadget X", price=49.99, stock=10,  category="gadgets"),
    4: Product(id=4, name="Gadget Y", price=0.99,  stock=0,   category="gadgets"),  # out of stock
}
_orders: dict[str, Order] = {}

TAX_RATE = 0.08


def get_product(product_id: int) -> Product:
    cached = get_cache(f"product:{product_id}")
    if cached:
        return cached
    product = _products.get(product_id)
    if not product:
        raise NotFoundError("Product", product_id)
    set_cache(f"product:{product_id}", product, ttl=60)
    return product


def check_stock(product_id: int, quantity: int) -> bool:
    product = get_product(product_id)
    if not product.is_available():
        raise StockError(product_id, quantity, 0)
    if product.stock < quantity:
        raise StockError(product_id, quantity, product.stock)
    return True


def calculate_tax(amount: float, rate: float = TAX_RATE) -> float:
    if rate < 0 or rate > 1:
        raise ValidationError("rate", f"tax rate must be 0-1, got {rate}")
    return round(amount * rate, 2)


def apply_discount(amount: float, discount_pct: float) -> float:
    if discount_pct < 0 or discount_pct > 100:
        raise ValidationError("discount_pct", "must be 0-100")
    return round(amount * (1 - discount_pct / 100), 2)


def compute_total(items: list[dict], discount_pct: float = 0.0) -> dict:
    validate_order_items(items)
    subtotal = sum(i["quantity"] * i["unit_price"] for i in items)
    discounted = apply_discount(subtotal, discount_pct)
    tax = calculate_tax(discounted)
    total = round(discounted + tax, 2)
    return {"subtotal": round(subtotal, 2), "discount": round(subtotal - discounted, 2),
            "tax": tax, "total": total}


def create_order(user_id: int, items: list[dict], discount_pct: float = 0.0) -> Order:
    validate_order_items(items)
    for item in items:
        check_stock(item["product_id"], item["quantity"])
    order_items = [OrderItem(product_id=i["product_id"], quantity=i["quantity"],
                             unit_price=i["unit_price"]) for i in items]
    order_id = str(uuid.uuid4())[:8]
    order = Order(id=order_id, user_id=user_id, items=order_items, discount_pct=discount_pct)
    _orders[order_id] = order
    # Deduct stock
    for item in items:
        _products[item["product_id"]].stock -= item["quantity"]
        invalidate(f"product:{item['product_id']}")
    return order


def get_order(order_id: str) -> Order:
    order = _orders.get(order_id)
    if not order:
        raise NotFoundError("Order", order_id)
    return order


def cancel_order(order_id: str) -> bool:
    order = get_order(order_id)
    if order.status == "cancelled":
        raise ValidationError("order_id", "order is already cancelled")
    if order.status == "delivered":
        raise ValidationError("order_id", "cannot cancel delivered order")
    # Restore stock
    for item in order.items:
        if item.product_id in _products:
            _products[item.product_id].stock += item.quantity
            invalidate(f"product:{item.product_id}")
    order.status = "cancelled"
    return True


def get_order_summary(user_id: int) -> dict:
    user_orders = [o for o in _orders.values() if o.user_id == user_id]
    if not user_orders:
        return {"user_id": user_id, "order_count": 0, "total_spent": 0.0, "statuses": {}}
    total_spent = sum(o.net_total() for o in user_orders)
    statuses: dict[str, int] = {}
    for o in user_orders:
        statuses[o.status] = statuses.get(o.status, 0) + 1
    return {
        "user_id": user_id,
        "order_count": len(user_orders),
        "total_spent": round(total_spent, 2),
        "avg_order_value": round(total_spent / len(user_orders), 2),
        "statuses": statuses,
    }
