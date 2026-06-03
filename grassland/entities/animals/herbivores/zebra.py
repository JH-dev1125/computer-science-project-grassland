from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from grassland.entities.animals.carnivores.lion import Lion

from grassland.entities.animals.herbivores.herbivore import Herbivore
from grassland.geometry import Vec2


class Zebra(Herbivore):
    def __init__(self, position: Vec2):
        super().__init__("Zebra", position, (232, 232, 218), 78.0, 86.0, 7.0, 185.0)
        self.zigzag_timer = 0.0

    def flee_from_lion(self, lion: "Lion", dt: float) -> None:
        self.fight_or_flight(lion, None, dt)
        self.action_text = "zigzag"
