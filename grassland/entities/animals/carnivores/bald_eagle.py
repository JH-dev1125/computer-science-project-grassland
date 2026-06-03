from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from grassland.world import World
from grassland.entities.animals.carnivores.carnivore import Carnivore
from grassland.geometry import Vec2


class BaldEagle(Carnivore):
    def __init__(self, position: Vec2):
        super().__init__("Bald_Eagle", position, (92, 82, 63), 58.0, 104.0, 10.0, 260.0)
        self.radius = 14.0
        self.is_flying = False

    def fly(self) -> None:
        self.is_flying = True
        self.action_text = "fly"

    def behave(self, world: "World", dt: float) -> bool:
        lion = world.nearest_named("Lion", self.position, 90.0)
        if lion is not None:
            self.fly()
            self.move_away_from(lion.position, self.speed)
            return True
        return super().behave(world, dt)
