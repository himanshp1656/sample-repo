"""
overloads.py — @typing.overload stubs + real implementations.

@overload stubs are skipped by our parser (they have no body).
Only the real implementation (no decorator) is indexed.
"""
from __future__ import annotations

from typing import overload, Union, List, Optional


# ── Function overload ─────────────────────────────────────────────────────────

@overload
def parse_id(value: str) -> int: ...          # stub — skipped by crawler

@overload
def parse_id(value: int) -> int: ...          # stub — skipped by crawler

def parse_id(value: Union[str, int]) -> int:  # real implementation — indexed
    """Parse a string or int into an int ID."""
    if isinstance(value, str):
        return int(value.strip())
    return value


@overload
def coerce(value: str, target: type) -> str: ...
@overload
def coerce(value: int, target: type) -> int: ...
@overload
def coerce(value: float, target: type) -> float: ...

def coerce(value, target):
    """Coerce value to target type."""
    return target(value)


# ── Method overloads on a class ───────────────────────────────────────────────

class DataStore:
    """
    A typed key-value store.
    get() is overloaded: with a default returns T, without may return None.
    """

    def __init__(self) -> None:
        self._data: dict = {}

    @overload
    def get(self, key: str) -> Optional[object]: ...
    @overload
    def get(self, key: str, default: object) -> object: ...

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value: object) -> None:
        self._data[key] = value

    @overload
    def pop(self, key: str) -> object: ...
    @overload
    def pop(self, key: str, default: object) -> object: ...

    def pop(self, key: str, *args):
        return self._data.pop(key, *args)

    @overload
    def update(self, data: dict) -> None: ...
    @overload
    def update(self, key: str, value: object) -> None: ...

    def update(self, data_or_key, value=None):
        if isinstance(data_or_key, dict):
            self._data.update(data_or_key)
        else:
            self._data[data_or_key] = value


# ── Overloaded __init__ pattern via classmethods ──────────────────────────────

class Interval:
    """
    Python can't overload __init__ directly, so the idiomatic pattern is
    to use @classmethod factory methods.
    """

    def __init__(self, start: float, end: float) -> None:
        if start > end:
            raise ValueError("start must be <= end")
        self.start = start
        self.end = end

    @classmethod
    def from_center(cls, center: float, half_width: float) -> "Interval":
        return cls(center - half_width, center + half_width)

    @classmethod
    def from_string(cls, s: str) -> "Interval":
        """Parse '1.0-5.0' into Interval(1.0, 5.0)."""
        lo, hi = s.split("-")
        return cls(float(lo), float(hi))

    @classmethod
    def unit(cls) -> "Interval":
        return cls(0.0, 1.0)

    def length(self) -> float:
        return self.end - self.start

    def contains(self, value: float) -> bool:
        return self.start <= value <= self.end

    def overlaps(self, other: "Interval") -> bool:
        return self.start <= other.end and other.start <= self.end

    def __repr__(self) -> str:
        return f"Interval({self.start}, {self.end})"


# ── Multiple dispatch simulation ──────────────────────────────────────────────

class Serialiser:
    """
    Simulates dispatch on type using overload stubs for type-checker
    satisfaction while the real impl uses isinstance.
    """

    @overload
    def serialise(self, value: str) -> str: ...
    @overload
    def serialise(self, value: int) -> str: ...
    @overload
    def serialise(self, value: list) -> str: ...
    @overload
    def serialise(self, value: dict) -> str: ...

    def serialise(self, value) -> str:
        import json
        if isinstance(value, (str, int, float, bool)):
            return json.dumps(value)
        return json.dumps(value, default=str)

    def deserialise(self, raw: str) -> object:
        import json
        return json.loads(raw)
