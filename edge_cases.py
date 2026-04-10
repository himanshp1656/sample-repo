"""
edge_cases.py — Tricky Python patterns that stress-test the AST crawler:

  • Lambda functions (anonymous, not indexed)
  • Functions inside functions (closures)
  • Conditional function definitions
  • Functions returned from functions
  • Class inside a function
  • Deeply nested calls
  • *args/**kwargs forwarding
  • Module-level code that calls functions
  • __all__ exports
  • Multiple assignment targets
  • Walrus operator in calls
  • Decorated functions with arguments
  • Late binding in closures (classic gotcha)
"""
from __future__ import annotations

from functools import wraps, lru_cache
from typing import Any, Callable, Dict, List, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

__all__ = [
    "retry",
    "memoize",
    "make_counter",
    "deep_caller",
    "ClassFactory",
]


# ── Parameterised decorator ───────────────────────────────────────────────────

def retry(max_attempts: int = 3, exceptions: tuple = (Exception,)) -> Callable[[F], F]:
    """Decorator factory — retry a function up to max_attempts times."""
    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Optional[Exception] = None
            for attempt in range(max_attempts):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
            raise RuntimeError(f"Failed after {max_attempts} attempts") from last_exc
        return wrapper  # type: ignore[return-value]
    return decorator


def rate_limit(calls_per_second: float) -> Callable[[F], F]:
    """Decorator factory — limits call rate."""
    import time
    min_interval = 1.0 / calls_per_second
    last: Dict[str, float] = {}

    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = fn.__qualname__
            now = time.monotonic()
            elapsed = now - last.get(key, 0)
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            last[key] = time.monotonic()
            return fn(*args, **kwargs)
        return wrapper  # type: ignore[return-value]
    return decorator


# ── Closure / function factory ────────────────────────────────────────────────

def make_counter(start: int = 0, step: int = 1) -> Callable[[], int]:
    """Returns a closure — each call increments a private counter."""
    count = [start]   # list to allow mutation from inner function

    def counter() -> int:
        val = count[0]
        count[0] += step
        return val

    return counter


def make_adder(n: int) -> Callable[[int], int]:
    """Late-binding closure — n is captured by reference (corrected)."""
    def add(x: int) -> int:
        return x + n
    return add


def make_multipliers(count: int) -> List[Callable[[int], int]]:
    """Classic closure-gotcha FIXED using default-arg capture."""
    return [lambda x, i=i: x * i for i in range(count)]


# ── Function inside function ──────────────────────────────────────────────────

def process_pipeline(data: List[Any], steps: List[str]) -> List[Any]:
    """Contains helper functions defined locally."""

    def _validate(item: Any) -> bool:
        return item is not None

    def _transform(item: Any) -> Any:
        return str(item).strip()

    def _filter_empty(item: Any) -> bool:
        return bool(item)

    result = [item for item in data if _validate(item)]
    if "transform" in steps:
        result = [_transform(item) for item in result]
    if "filter" in steps:
        result = [item for item in result if _filter_empty(item)]
    return result


# ── Conditional function definition ──────────────────────────────────────────

import sys

if sys.platform == "win32":
    def get_path_separator() -> str:
        return "\\"
else:
    def get_path_separator() -> str:
        return "/"


# ── lru_cache + recursive ─────────────────────────────────────────────────────

@lru_cache(maxsize=256)
def fibonacci(n: int) -> int:
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)   # recursive self-call


@lru_cache(maxsize=None)
def count_ways(n: int, k: int) -> int:
    """Count ways to reach step n with max jump k (DP)."""
    if n == 0:
        return 1
    return sum(count_ways(n - i, k) for i in range(1, min(n, k) + 1))


# ── Deep call chain ───────────────────────────────────────────────────────────

def _level3(x: int) -> int:
    return x * 2


def _level2(x: int) -> int:
    return _level3(x + 1)


def _level1(x: int) -> int:
    return _level2(x - 1)


def deep_caller(x: int) -> int:
    """Entry point — calls _level1 → _level2 → _level3."""
    return _level1(x)


# ── *args/**kwargs forwarding ─────────────────────────────────────────────────

def memoize(fn: F) -> F:
    cache: Dict[Any, Any] = {}

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        key = (args, tuple(sorted(kwargs.items())))
        if key not in cache:
            cache[key] = fn(*args, **kwargs)
        return cache[key]

    return wrapper  # type: ignore[return-value]


@memoize
def expensive_compute(x: int, *, multiplier: int = 1) -> int:
    import time
    time.sleep(0.001)   # simulated work
    return x * multiplier


# ── Class inside a function ───────────────────────────────────────────────────

def ClassFactory(base_name: str, fields: List[str]) -> type:
    """Dynamically creates a class with the given fields."""

    class DynamicClass:
        def __init__(self, **kwargs: Any) -> None:
            for f in fields:
                setattr(self, f, kwargs.get(f))

        def to_dict(self) -> Dict[str, Any]:
            return {f: getattr(self, f) for f in fields}

        def __repr__(self) -> str:
            parts = ", ".join(f"{f}={getattr(self, f)!r}" for f in fields)
            return f"{base_name}({parts})"

    DynamicClass.__name__ = base_name
    DynamicClass.__qualname__ = base_name
    return DynamicClass


# ── Walrus operator edge case ─────────────────────────────────────────────────

def find_first_even(numbers: List[int]) -> Optional[int]:
    """Uses walrus operator — parsing edge case."""
    return next((n for n in numbers if (rem := n % 2) == 0), None)


# ── Module-level code (calls at import time) ──────────────────────────────────

_default_counter = make_counter(start=1000)    # module-level call
_fib_10 = fibonacci(10)                        # module-level call, populates lru_cache


# ── Multiple return types ─────────────────────────────────────────────────────

def parse_value(raw: str) -> int | float | str:
    """Returns different types based on input."""
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        return raw
