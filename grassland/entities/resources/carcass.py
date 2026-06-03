from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from grassland.entities.resources.resource import Resource
from grassland.geometry import Vec2

if TYPE_CHECKING:
    from grassland.entities.animals.animal import Animal


class Carcass(Resource):
    def __init__(self, position: Vec2, amount: float = 85.0):
        super().__init__(
            name="Carcass",
            position=position,
            amount=amount,
            color=(118, 72, 44),
        )
        self.radius = 20
        self.carried_by: Optional["Animal"] = None
        self.being_eaten_by: Optional["Animal"] = None

    def reduce_hunger(self, animal: "Animal") -> None:
        taken = self.consume(22)
        animal.hunger = max(0.0, animal.hunger - taken)
