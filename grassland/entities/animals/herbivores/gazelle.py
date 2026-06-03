from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from grassland.entities.base import Entity

from grassland.entities.animals.herbivores.herbivore import Herbivore
from grassland.geometry import Vec2


class Gazelle(Herbivore):
    def __init__(self, position: Vec2):
        super().__init__("Gazelle", position, (205, 166, 96), 52.0, 96.0, 5.0, 205.0)

    def zigzag(self, threat: "Entity") -> None:
        self.move_away_from(threat.position, self.flee_speed)
        self.action_text = "zigzag"
