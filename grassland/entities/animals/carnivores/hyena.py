from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from grassland.entities.base import Entity

from grassland.entities.animals.carnivores.carnivore import Carnivore
from grassland.geometry import Vec2


class Hyena(Carnivore):
    def __init__(self, position: Vec2):
        super().__init__("Hyena", position, (156, 126, 82), 86.0, 76.0, 15.0, 215.0)

    def steal_prey(self, carcass: "Entity") -> None:
        c: Any = carcass
        if hasattr(carcass, "being_eaten_by"):
            c.being_eaten_by = self
        self.action_text = "steal"
