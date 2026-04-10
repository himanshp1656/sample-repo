"""
abstract_classes.py — Abstract Base Classes (ABC).

ABCs enforce that subclasses implement required methods.
Unlike Protocols (structural), ABC inheritance is explicit (nominal).
"""
from __future__ import annotations

from abc import ABC, abstractmethod, abstractproperty
from typing import List, Optional


# ── Simple ABC ────────────────────────────────────────────────────────────────

class Shape(ABC):
    """Every Shape must know its area and perimeter."""

    def __init__(self, color: str = "black") -> None:
        self.color = color

    @abstractmethod
    def area(self) -> float:
        ...

    @abstractmethod
    def perimeter(self) -> float:
        ...

    def describe(self) -> str:
        return (
            f"{self.__class__.__name__}(color={self.color}, "
            f"area={self.area():.2f}, perimeter={self.perimeter():.2f})"
        )


# ── Concrete subclasses ───────────────────────────────────────────────────────

class Circle(Shape):
    def __init__(self, radius: float, color: str = "black") -> None:
        super().__init__(color)
        self.radius = radius

    def area(self) -> float:
        import math
        return math.pi * self.radius ** 2

    def perimeter(self) -> float:
        import math
        return 2 * math.pi * self.radius


class Rectangle(Shape):
    def __init__(self, width: float, height: float, color: str = "black") -> None:
        super().__init__(color)
        self.width = width
        self.height = height

    def area(self) -> float:
        return self.width * self.height

    def perimeter(self) -> float:
        return 2 * (self.width + self.height)

    def is_square(self) -> bool:
        return self.width == self.height


class Triangle(Shape):
    def __init__(self, a: float, b: float, c: float, color: str = "black") -> None:
        super().__init__(color)
        self.a, self.b, self.c = a, b, c

    def area(self) -> float:
        s = self.perimeter() / 2
        return (s * (s - self.a) * (s - self.b) * (s - self.c)) ** 0.5

    def perimeter(self) -> float:
        return self.a + self.b + self.c


# ── ABC with abstract property ────────────────────────────────────────────────

class Storage(ABC):
    @property
    @abstractmethod
    def capacity(self) -> int:
        ...

    @abstractmethod
    def read(self, key: str) -> Optional[bytes]:
        ...

    @abstractmethod
    def write(self, key: str, data: bytes) -> None:
        ...

    def copy(self, src: str, dst: str) -> None:
        data = self.read(src)
        if data is not None:
            self.write(dst, data)


class MemoryStorage(Storage):
    def __init__(self, max_bytes: int = 1024 * 1024) -> None:
        self._max = max_bytes
        self._data: dict[str, bytes] = {}

    @property
    def capacity(self) -> int:
        return self._max

    def read(self, key: str) -> Optional[bytes]:
        return self._data.get(key)

    def write(self, key: str, data: bytes) -> None:
        self._data[key] = data


# ── Multi-level ABC chain ─────────────────────────────────────────────────────

class Animal(ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def speak(self) -> str:
        ...

    def introduce(self) -> str:
        return f"I am {self.name} and I say: {self.speak()}"


class Mammal(Animal, ABC):
    """Intermediate ABC — still abstract."""

    @abstractmethod
    def breathe(self) -> str:
        ...

    def is_warm_blooded(self) -> bool:
        return True


class Dog(Mammal):
    def speak(self) -> str:
        return "Woof!"

    def breathe(self) -> str:
        return "inhale/exhale with lungs"

    def fetch(self, item: str) -> str:
        return f"{self.name} fetches {item}"


class Cat(Mammal):
    def speak(self) -> str:
        return "Meow!"

    def breathe(self) -> str:
        return "inhale/exhale with lungs"

    def purr(self) -> str:
        return f"{self.name} purrs..."


# ── ABC + mixin ───────────────────────────────────────────────────────────────

class LogMixin:
    """Stateless mixin — adds logging to any class."""

    def log(self, message: str) -> None:
        print(f"[{self.__class__.__name__}] {message}")


class LoggedStorage(LogMixin, MemoryStorage):
    def write(self, key: str, data: bytes) -> None:
        self.log(f"write {key!r} ({len(data)} bytes)")
        super().write(key, data)

    def read(self, key: str) -> Optional[bytes]:
        result = super().read(key)
        self.log(f"read {key!r} → {'HIT' if result is not None else 'MISS'}")
        return result


def total_area(shapes: List[Shape]) -> float:
    return sum(s.area() for s in shapes)
