"""
composition.py — Composition patterns: classes instantiating other classes,
dependency injection, builder pattern, and observer pattern.

Each pattern exercises a different cross-class relationship:
  - instantiates (Foo creates Bar())
  - uses (Foo accepts Bar as a parameter)
  - owns (Foo stores Bar as an attribute)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, Set


# ── Logger (used by many) ─────────────────────────────────────────────────────

class Logger:
    def __init__(self, name: str) -> None:
        self.name = name

    def info(self, msg: str) -> None:
        print(f"[INFO][{self.name}] {msg}")

    def error(self, msg: str) -> None:
        print(f"[ERR ][{self.name}] {msg}")


# ── Cache (composed into services) ───────────────────────────────────────────

class Cache:
    def __init__(self, max_size: int = 256) -> None:
        self._store: Dict[str, object] = {}
        self.max_size = max_size

    def get(self, key: str) -> Optional[object]:
        return self._store.get(key)

    def set(self, key: str, value: object) -> None:
        if len(self._store) >= self.max_size:
            oldest = next(iter(self._store))
            del self._store[oldest]
        self._store[key] = value

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()


# ── UserService: composes Logger + Cache, instantiates them internally ────────

class UserService:
    """Owns Logger and Cache — instantiates them in __init__."""

    def __init__(self, cache_size: int = 128) -> None:
        self._log = Logger("UserService")          # instantiates Logger
        self._cache = Cache(cache_size)            # instantiates Cache
        self._users: Dict[str, Dict] = {}

    def create_user(self, id: str, name: str, email: str) -> Dict:
        user = {"id": id, "name": name, "email": email}
        self._users[id] = user
        self._cache.set(id, user)
        self._log.info(f"Created user {id}")
        return user

    def get_user(self, id: str) -> Optional[Dict]:
        cached = self._cache.get(id)
        if cached is not None:
            return cached                          # type: ignore[return-value]
        user = self._users.get(id)
        if user:
            self._cache.set(id, user)
        return user

    def delete_user(self, id: str) -> bool:
        if id in self._users:
            del self._users[id]
            self._cache.invalidate(id)
            self._log.info(f"Deleted user {id}")
            return True
        return False


# ── Dependency injection variant ──────────────────────────────────────────────

class OrderRepository:
    def __init__(self) -> None:
        self._orders: Dict[str, Dict] = {}

    def save(self, order: Dict) -> Dict:
        self._orders[order["id"]] = order
        return order

    def find(self, id: str) -> Optional[Dict]:
        return self._orders.get(id)

    def list_by_user(self, user_id: str) -> List[Dict]:
        return [o for o in self._orders.values() if o.get("user_id") == user_id]


class OrderService:
    """Receives Logger and OrderRepository via injection — does NOT instantiate them."""

    def __init__(self, repo: OrderRepository, logger: Logger) -> None:
        self._repo = repo
        self._log = logger

    def place_order(self, user_id: str, items: List[Dict]) -> Dict:
        import uuid
        total = sum(i.get("price", 0) * i.get("qty", 1) for i in items)
        order = {"id": str(uuid.uuid4()), "user_id": user_id, "items": items, "total": total}
        saved = self._repo.save(order)
        self._log.info(f"Order {saved['id']} placed for user {user_id}, total={total}")
        return saved

    def cancel_order(self, order_id: str) -> bool:
        order = self._repo.find(order_id)
        if not order:
            return False
        order["status"] = "cancelled"
        self._repo.save(order)
        self._log.info(f"Order {order_id} cancelled")
        return True


# ── Builder pattern ───────────────────────────────────────────────────────────

class QueryBuilder:
    """Builds SQL-like query strings step by step."""

    class WhereClause:
        def __init__(self, column: str, op: str, value: object) -> None:
            self.column = column
            self.op = op
            self.value = value

        def __str__(self) -> str:
            return f"{self.column} {self.op} {self.value!r}"

    def __init__(self, table: str) -> None:
        self._table = table
        self._columns: List[str] = ["*"]
        self._where: List[QueryBuilder.WhereClause] = []
        self._limit: Optional[int] = None
        self._offset: int = 0
        self._order_by: Optional[str] = None

    def select(self, *columns: str) -> "QueryBuilder":
        self._columns = list(columns)
        return self

    def where(self, column: str, op: str, value: object) -> "QueryBuilder":
        self._where.append(QueryBuilder.WhereClause(column, op, value))
        return self

    def limit(self, n: int) -> "QueryBuilder":
        self._limit = n
        return self

    def offset(self, n: int) -> "QueryBuilder":
        self._offset = n
        return self

    def order_by(self, column: str) -> "QueryBuilder":
        self._order_by = column
        return self

    def build(self) -> str:
        cols = ", ".join(self._columns)
        sql = f"SELECT {cols} FROM {self._table}"
        if self._where:
            clauses = " AND ".join(str(w) for w in self._where)
            sql += f" WHERE {clauses}"
        if self._order_by:
            sql += f" ORDER BY {self._order_by}"
        if self._limit is not None:
            sql += f" LIMIT {self._limit}"
        if self._offset:
            sql += f" OFFSET {self._offset}"
        return sql


# ── Observer pattern ──────────────────────────────────────────────────────────

class Event:
    def __init__(self, name: str, payload: Dict) -> None:
        self.name = name
        self.payload = payload


class EventBus:
    def __init__(self) -> None:
        self._handlers: Dict[str, List[Callable[[Event], None]]] = {}

    def subscribe(self, event_name: str, handler: Callable[[Event], None]) -> None:
        self._handlers.setdefault(event_name, []).append(handler)

    def unsubscribe(self, event_name: str, handler: Callable[[Event], None]) -> None:
        handlers = self._handlers.get(event_name, [])
        if handler in handlers:
            handlers.remove(handler)

    def publish(self, event: Event) -> None:
        for handler in self._handlers.get(event.name, []):
            handler(event)


class NotificationService:
    """Subscribes to EventBus events and sends notifications."""

    def __init__(self, bus: EventBus) -> None:
        self._bus = bus
        self._log = Logger("NotificationService")  # instantiates Logger
        bus.subscribe("user.created", self._on_user_created)
        bus.subscribe("order.placed", self._on_order_placed)

    def _on_user_created(self, event: Event) -> None:
        self._log.info(f"Welcome email → {event.payload.get('email')}")

    def _on_order_placed(self, event: Event) -> None:
        self._log.info(f"Order confirmation → order {event.payload.get('id')}")


class AuditService:
    """Also subscribes to the same bus — shows fan-out."""

    def __init__(self, bus: EventBus) -> None:
        self._bus = bus
        self._log = Logger("AuditService")        # instantiates Logger
        self._events: List[Event] = []
        bus.subscribe("user.created", self._record)
        bus.subscribe("order.placed", self._record)
        bus.subscribe("order.cancelled", self._record)

    def _record(self, event: Event) -> None:
        self._events.append(event)
        self._log.info(f"Audit: {event.name}")

    def recent(self, n: int = 10) -> List[Event]:
        return self._events[-n:]
