"""
inheritance.py — Single, multi-level, multiple, and diamond inheritance.

Demonstrates Python's MRO (Method Resolution Order) via C3 linearisation.
"""
from __future__ import annotations

from typing import Any


# ── Single inheritance ────────────────────────────────────────────────────────

class Vehicle:
    def __init__(self, make: str, model: str, year: int) -> None:
        self.make = make
        self.model = model
        self.year = year

    def start(self) -> str:
        return f"{self.make} {self.model} engine starts."

    def stop(self) -> str:
        return f"{self.make} {self.model} engine stops."

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.make!r}, {self.model!r}, {self.year})"


class Car(Vehicle):
    def __init__(self, make: str, model: str, year: int, doors: int = 4) -> None:
        super().__init__(make, model, year)
        self.doors = doors

    def honk(self) -> str:
        return "Beep beep!"


# ── Multi-level inheritance ───────────────────────────────────────────────────

class ElectricVehicle(Vehicle):
    def __init__(self, make: str, model: str, year: int, battery_kwh: float) -> None:
        super().__init__(make, model, year)
        self.battery_kwh = battery_kwh

    def charge(self) -> str:
        return f"Charging {self.battery_kwh} kWh battery..."

    def start(self) -> str:          # override
        return f"{self.make} {self.model} silently powers on."


class ElectricCar(Car, ElectricVehicle):
    """Diamond-safe: Car → Vehicle, ElectricVehicle → Vehicle."""

    def __init__(
        self, make: str, model: str, year: int, battery_kwh: float, doors: int = 4
    ) -> None:
        # MRO: ElectricCar → Car → ElectricVehicle → Vehicle
        super().__init__(make, model, year, doors)
        self.battery_kwh = battery_kwh

    def range_km(self) -> float:
        return self.battery_kwh * 6.0          # rough estimate


class ElectricSUV(ElectricCar):
    def __init__(
        self, make: str, model: str, year: int, battery_kwh: float, awd: bool = True
    ) -> None:
        super().__init__(make, model, year, battery_kwh, doors=4)
        self.awd = awd

    def tow_capacity_kg(self) -> float:
        return 900.0 + (100.0 if self.awd else 0.0)


# ── Classic diamond ───────────────────────────────────────────────────────────

class A:
    def hello(self) -> str:
        return "A.hello"

    def shared(self) -> str:
        return "A.shared"


class B(A):
    def hello(self) -> str:          # override
        return f"B.hello → {super().hello()}"


class C(A):
    def hello(self) -> str:          # override
        return f"C.hello → {super().hello()}"

    def shared(self) -> str:         # override
        return "C.shared"


class D(B, C):
    """MRO: D → B → C → A.  B.hello calls C.hello via super()."""

    def hello(self) -> str:          # override
        return f"D.hello → {super().hello()}"


# ── Mixin pattern ─────────────────────────────────────────────────────────────

class TimestampMixin:
    """Adds created_at / updated_at to any model class."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        import time
        self.created_at: float = time.time()
        self.updated_at: float = self.created_at

    def touch(self) -> None:
        import time
        self.updated_at = time.time()


class SoftDeleteMixin:
    """Adds is_deleted flag; delete() marks instead of removing."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.is_deleted: bool = False

    def delete(self) -> None:
        self.is_deleted = True

    def restore(self) -> None:
        self.is_deleted = False


class BaseModel:
    def __init__(self, id: str) -> None:
        self.id = id

    def validate(self) -> bool:
        return bool(self.id)


class AuditedModel(TimestampMixin, SoftDeleteMixin, BaseModel):
    """Composes all three mixins via cooperative multiple inheritance."""

    def __init__(self, id: str, owner: str) -> None:
        super().__init__(id)
        self.owner = owner

    def summary(self) -> dict:
        return {
            "id": self.id,
            "owner": self.owner,
            "deleted": self.is_deleted,
            "created_at": self.created_at,
        }


# ── Method resolution helpers ─────────────────────────────────────────────────

def show_mro(cls: type) -> list[str]:
    return [c.__name__ for c in cls.__mro__]


def create_fleet() -> list[Vehicle]:
    return [
        Car("Toyota", "Corolla", 2020),
        ElectricCar("Tesla", "Model 3", 2023, battery_kwh=75.0),
        ElectricSUV("Rivian", "R1S", 2024, battery_kwh=135.0),
    ]
