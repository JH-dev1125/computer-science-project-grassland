from __future__ import annotations

from grassland.entities.base import Entity
from grassland.geometry import Vec2


class Resource(Entity):
    def __init__(self, name: str, position: Vec2, amount: float, color: tuple[int, int, int]):
        super().__init__(name=name, position=position, radius=18, color=color)
        self.amount = amount
        self.max_amount = amount
        self.kind = "resource"

    def consume(self, amount: float) -> float:
        taken = min(self.amount, amount)
        self.amount -= taken
        if self.amount <= 0:
            self.delete()
        return taken

    def regenerate(self, amount: float) -> None:
        self.amount = min(self.max_amount, self.amount + amount)
        self.alive = True

    def delete(self) -> None:
        self.alive = False

