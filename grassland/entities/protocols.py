from __future__ import annotations

from typing import Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from grassland.entities.animals.animal import Animal


@runtime_checkable
class Consumable(Protocol):
    """consume(amount) 을 통해 부분 섭취가 가능한 객체."""

    def consume(self, amount: float) -> float:
        """실제로 섭취된 양을 반환한다."""
        ...


@runtime_checkable
class Drinkable(Protocol):
    """동물이 음용할 수 있는 객체 (water puddle, lake 등)."""

    def reduce_thirst(self, animal: "Animal") -> None:
        """animal 의 thirst 를 감소시킨다."""
        ...
