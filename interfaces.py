"""
interfaces.py — Python Protocols (the closest thing to interfaces).

Protocol classes define structural subtyping: any class that has the
required methods/attributes satisfies the Protocol, even without
explicitly inheriting from it (duck typing / structural typing).
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable, List, Optional


# ── Simple Protocol ───────────────────────────────────────────────────────────

@runtime_checkable
class Serializable(Protocol):
    """Anything that can be serialised to / from a dict."""

    def to_dict(self) -> dict:
        ...

    @classmethod
    def from_dict(cls, data: dict) -> "Serializable":
        ...


# ── Protocol with inheritance ─────────────────────────────────────────────────

class Identifiable(Protocol):
    """Has a stable unique ID."""

    @property
    def id(self) -> str:
        ...


class Persistable(Identifiable, Protocol):
    """Can be saved and loaded; also must be identifiable."""

    def save(self) -> None:
        ...

    def delete(self) -> None:
        ...


# ── Generic Protocol ──────────────────────────────────────────────────────────

from typing import TypeVar, Generic

T = TypeVar("T")
K = TypeVar("K")


class Repository(Protocol[T]):
    """Generic repository interface — CRUD over entity T."""

    def get(self, id: str) -> Optional[T]:
        ...

    def list(self) -> List[T]:
        ...

    def save(self, entity: T) -> T:
        ...

    def delete(self, id: str) -> None:
        ...


# ── Callable Protocol ─────────────────────────────────────────────────────────

class Transformer(Protocol[T, K]):
    """Anything callable that transforms T → K."""

    def __call__(self, value: T) -> K:
        ...


# ── Concrete implementations (structural — no explicit inherit needed) ─────────

class UserRecord:
    """Satisfies Serializable + Identifiable structurally."""

    def __init__(self, user_id: str, name: str) -> None:
        self._id = user_id
        self.name = name

    @property
    def id(self) -> str:
        return self._id

    def to_dict(self) -> dict:
        return {"id": self._id, "name": self.name}

    @classmethod
    def from_dict(cls, data: dict) -> "UserRecord":
        return cls(data["id"], data["name"])

    def save(self) -> None:
        print(f"Saving user {self._id}")

    def delete(self) -> None:
        print(f"Deleting user {self._id}")


class InMemoryUserRepo:
    """Concrete repository satisfying Repository[UserRecord]."""

    def __init__(self) -> None:
        self._store: dict[str, UserRecord] = {}

    def get(self, id: str) -> Optional[UserRecord]:
        return self._store.get(id)

    def list(self) -> List[UserRecord]:
        return list(self._store.values())

    def save(self, entity: UserRecord) -> UserRecord:
        self._store[entity.id] = entity
        return entity

    def delete(self, id: str) -> None:
        self._store.pop(id, None)


def process_serializable(obj: Serializable) -> dict:
    """Accepts anything that satisfies Serializable (structural)."""
    return obj.to_dict()


def persist_all(repo: Repository[UserRecord], records: List[UserRecord]) -> None:
    for r in records:
        repo.save(r)
