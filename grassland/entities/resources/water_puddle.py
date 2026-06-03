from __future__ import annotations

from typing import TYPE_CHECKING

from grassland.entities.resources.resource import Resource
from grassland.geometry import Vec2

if TYPE_CHECKING:
    from grassland.entities.animals.animal import Animal


class WaterPuddle(Resource):
    def __init__(self, position: Vec2, amount: float = 100.0):
        super().__init__(
            name="Water_Puddle",
            position=position,
            amount=amount,
            color=(65, 145, 208),
        )
        self.radius = 28

    def reduce_thirst(self, animal: "Animal") -> None:
        taken = self.consume(18)
        animal.thirst = max(0.0, animal.thirst - taken)

    def fill_rain(self) -> None:
        self.regenerate(35)
