"""
generics.py — Generic classes using TypeVar and Generic[T].

Shows parameterised containers, bounded TypeVars, multiple type params,
and generic ABCs.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    Generic, TypeVar, Iterator, List, Optional,
    Callable, Tuple, Dict, Iterable
)

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


# ── Simple generic container ──────────────────────────────────────────────────

class Stack(Generic[T]):
    """LIFO stack parameterised on element type T."""

    def __init__(self) -> None:
        self._items: List[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self) -> T:
        if not self._items:
            raise IndexError("peek at empty stack")
        return self._items[-1]

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(reversed(self._items))


class Queue(Generic[T]):
    """FIFO queue."""

    def __init__(self) -> None:
        self._items: List[T] = []

    def enqueue(self, item: T) -> None:
        self._items.append(item)

    def dequeue(self) -> T:
        if not self._items:
            raise IndexError("dequeue from empty queue")
        return self._items.pop(0)

    def peek(self) -> T:
        return self._items[0]

    def __len__(self) -> int:
        return len(self._items)


# ── Bounded TypeVar ───────────────────────────────────────────────────────────

from typing import SupportsFloat

N = TypeVar("N", int, float)    # constrained TypeVar


class Interval(Generic[N]):
    def __init__(self, lo: N, hi: N) -> None:
        self.lo = lo
        self.hi = hi

    def contains(self, value: N) -> bool:
        return self.lo <= value <= self.hi

    def clamp(self, value: N) -> N:
        if value < self.lo:
            return self.lo
        if value > self.hi:
            return self.hi
        return value

    def length(self) -> float:
        return float(self.hi) - float(self.lo)


# ── Multiple type params ──────────────────────────────────────────────────────

class Either(Generic[T, K]):
    """A value that is either Left[T] or Right[K] (functional Either monad)."""

    def __init__(self, left: Optional[T] = None, right: Optional[K] = None) -> None:
        assert (left is None) != (right is None), "Exactly one of left/right"
        self._left = left
        self._right = right

    @classmethod
    def left(cls, value: T) -> "Either[T, K]":
        return cls(left=value)

    @classmethod
    def right(cls, value: K) -> "Either[T, K]":
        return cls(right=value)

    def is_left(self) -> bool:
        return self._left is not None

    def is_right(self) -> bool:
        return self._right is not None

    def get_left(self) -> T:
        if self._left is None:
            raise ValueError("Not a Left")
        return self._left

    def get_right(self) -> K:
        if self._right is None:
            raise ValueError("Not a Right")
        return self._right

    def map_right(self, fn: Callable[[K], V]) -> "Either[T, V]":
        if self.is_right():
            return Either.right(fn(self.get_right()))  # type: ignore[arg-type]
        return Either.left(self.get_left())             # type: ignore[arg-type]


# ── Generic ABC ───────────────────────────────────────────────────────────────

class Mapper(ABC, Generic[T, K]):
    """Abstract transformation T → K."""

    @abstractmethod
    def map(self, value: T) -> K:
        ...

    def map_all(self, values: Iterable[T]) -> List[K]:
        return [self.map(v) for v in values]


class StringToInt(Mapper[str, int]):
    def map(self, value: str) -> int:
        return int(value.strip())


class IntToStr(Mapper[int, str]):
    def __init__(self, fmt: str = "{}") -> None:
        self.fmt = fmt

    def map(self, value: int) -> str:
        return self.fmt.format(value)


# ── Generic result type ───────────────────────────────────────────────────────

class Result(Generic[T]):
    """
    Rust-style Result: either Ok(value) or Err(message).
    Avoids try/except explosion in calling code.
    """

    def __init__(self, value: Optional[T], error: Optional[str]) -> None:
        self._value = value
        self._error = error

    @classmethod
    def ok(cls, value: T) -> "Result[T]":
        return cls(value, None)

    @classmethod
    def err(cls, message: str) -> "Result[T]":
        return cls(None, message)

    def is_ok(self) -> bool:
        return self._error is None

    def unwrap(self) -> T:
        if self._error:
            raise RuntimeError(self._error)
        return self._value  # type: ignore[return-value]

    def unwrap_or(self, default: T) -> T:
        return self._value if self.is_ok() else default  # type: ignore[return-value]

    def map(self, fn: Callable[[T], K]) -> "Result[K]":
        if self.is_ok():
            try:
                return Result.ok(fn(self.unwrap()))
            except Exception as e:
                return Result.err(str(e))
        return Result.err(self._error)  # type: ignore[arg-type]

    def and_then(self, fn: Callable[[T], "Result[K]"]) -> "Result[K]":
        if self.is_ok():
            return fn(self.unwrap())
        return Result.err(self._error)  # type: ignore[arg-type]


def safe_divide(a: float, b: float) -> Result[float]:
    if b == 0:
        return Result.err("Division by zero")
    return Result.ok(a / b)
