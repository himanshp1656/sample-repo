"""
advanced_classes.py — Nested classes, descriptors, __slots__, metaclasses,
class decorators, __init_subclass__, and async methods.
"""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type


# ── Nested classes ────────────────────────────────────────────────────────────

class BinaryTree:
    """BST with a nested Node class."""

    class Node:
        def __init__(self, value: int) -> None:
            self.value = value
            self.left: Optional["BinaryTree.Node"] = None
            self.right: Optional["BinaryTree.Node"] = None

        def is_leaf(self) -> bool:
            return self.left is None and self.right is None

    def __init__(self) -> None:
        self.root: Optional[BinaryTree.Node] = None

    def insert(self, value: int) -> None:
        self.root = self._insert(self.root, value)

    def _insert(self, node: Optional[Node], value: int) -> Node:
        if node is None:
            return BinaryTree.Node(value)
        if value < node.value:
            node.left = self._insert(node.left, value)
        elif value > node.value:
            node.right = self._insert(node.right, value)
        return node

    def contains(self, value: int) -> bool:
        cur = self.root
        while cur:
            if value == cur.value:
                return True
            cur = cur.left if value < cur.value else cur.right
        return False

    def inorder(self) -> List[int]:
        result: List[int] = []
        self._inorder(self.root, result)
        return result

    def _inorder(self, node: Optional[Node], result: List[int]) -> None:
        if node:
            self._inorder(node.left, result)
            result.append(node.value)
            self._inorder(node.right, result)


# ── Descriptors ───────────────────────────────────────────────────────────────

class Validator:
    """Non-data descriptor base for attribute validation."""

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name
        self.private = f"_{name}"

    def __get__(self, obj: Any, objtype: Any = None) -> Any:
        if obj is None:
            return self
        return getattr(obj, self.private, None)

    def __set__(self, obj: Any, value: Any) -> None:
        self.validate(value)
        setattr(obj, self.private, value)

    def validate(self, value: Any) -> None: ...


class PositiveInt(Validator):
    def validate(self, value: Any) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{self.name} must be a positive int, got {value!r}")


class NonEmptyStr(Validator):
    def validate(self, value: Any) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{self.name} must be a non-empty string, got {value!r}")


class Employee:
    name = NonEmptyStr()
    age = PositiveInt()
    salary = PositiveInt()

    def __init__(self, name: str, age: int, salary: int) -> None:
        self.name = name
        self.age = age
        self.salary = salary

    def give_raise(self, amount: int) -> None:
        self.salary += amount

    def __repr__(self) -> str:
        return f"Employee({self.name!r}, age={self.age}, salary={self.salary})"


# ── __slots__ ─────────────────────────────────────────────────────────────────

class SlottedPoint:
    """Uses __slots__ to avoid per-instance __dict__; saves memory."""
    __slots__ = ("x", "y")

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def distance(self) -> float:
        return (self.x ** 2 + self.y ** 2) ** 0.5

    def __repr__(self) -> str:
        return f"SlottedPoint({self.x}, {self.y})"


class SlottedPoint3D(SlottedPoint):
    __slots__ = ("z",)

    def __init__(self, x: float, y: float, z: float) -> None:
        super().__init__(x, y)
        self.z = z

    def distance(self) -> float:                   # override
        return (self.x ** 2 + self.y ** 2 + self.z ** 2) ** 0.5


# ── __init_subclass__ ─────────────────────────────────────────────────────────

class PluginBase:
    """
    __init_subclass__ is called whenever a class inherits from PluginBase.
    Used here to auto-register plugins.
    """
    _registry: Dict[str, Type["PluginBase"]] = {}

    def __init_subclass__(cls, plugin_name: str = "", **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if plugin_name:
            PluginBase._registry[plugin_name] = cls

    @classmethod
    def get(cls, name: str) -> Optional[Type["PluginBase"]]:
        return cls._registry.get(name)

    def run(self) -> str:
        raise NotImplementedError


class CsvPlugin(PluginBase, plugin_name="csv"):
    def run(self) -> str:
        return "Processing CSV"


class JsonPlugin(PluginBase, plugin_name="json"):
    def run(self) -> str:
        return "Processing JSON"


class XmlPlugin(PluginBase, plugin_name="xml"):
    def run(self) -> str:
        return "Processing XML"


# ── Async class methods ───────────────────────────────────────────────────────

class AsyncRepository(ABC):
    @abstractmethod
    async def fetch(self, id: str) -> Optional[Dict]:
        ...

    @abstractmethod
    async def save(self, record: Dict) -> Dict:
        ...

    async def fetch_or_create(self, id: str, defaults: Dict) -> Dict:
        existing = await self.fetch(id)
        if existing is not None:
            return existing
        return await self.save({"id": id, **defaults})


class InMemoryAsyncRepo(AsyncRepository):
    def __init__(self) -> None:
        self._store: Dict[str, Dict] = {}

    async def fetch(self, id: str) -> Optional[Dict]:
        await asyncio.sleep(0)               # simulate I/O
        return self._store.get(id)

    async def save(self, record: Dict) -> Dict:
        await asyncio.sleep(0)
        self._store[record["id"]] = record
        return record

    async def delete(self, id: str) -> bool:
        if id in self._store:
            del self._store[id]
            return True
        return False

    async def list_all(self) -> List[Dict]:
        await asyncio.sleep(0)
        return list(self._store.values())


# ── Singleton via metaclass ───────────────────────────────────────────────────

class SingletonMeta(type):
    _instances: Dict[type, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class AppConfig(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self.debug = False
        self.log_level = "INFO"
        self.max_connections = 10

    def update(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)


# ── Class decorator ───────────────────────────────────────────────────────────

def auto_repr(cls: type) -> type:
    """Class decorator that generates __repr__ from __init__ signature."""
    import inspect
    params = list(inspect.signature(cls.__init__).parameters.keys())[1:]  # skip self

    def __repr__(self) -> str:
        parts = [f"{p}={getattr(self, p, '?')!r}" for p in params]
        return f"{cls.__name__}({', '.join(parts)})"

    cls.__repr__ = __repr__
    return cls


@auto_repr
class Config:
    def __init__(self, host: str, port: int, tls: bool = False) -> None:
        self.host = host
        self.port = port
        self.tls = tls

    def url(self) -> str:
        scheme = "https" if self.tls else "http"
        return f"{scheme}://{self.host}:{self.port}"
