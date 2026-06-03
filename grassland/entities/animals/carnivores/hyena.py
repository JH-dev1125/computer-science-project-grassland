from __future__ import annotations

from grassland.entities.animals.carnivores.carnivore import Carnivore
from grassland.entities.resources.carcass import Carcass
from grassland.geometry import Vec2


class Hyena(Carnivore):
    def __init__(self, position: Vec2):
        super().__init__("Hyena", position, (156, 126, 82), 86.0, 76.0, 15.0, 215.0)

    def steal_prey(self, carcass: Carcass) -> None:
        carcass.being_eaten_by = self
        self.action_text = "steal"
