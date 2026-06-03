from __future__ import annotations

from typing import TYPE_CHECKING

from grassland.entities.animals.carnivores.carnivore import Carnivore
from grassland.entities.animals.herbivores.herbivore import Herbivore
from grassland.geometry import Vec2

if TYPE_CHECKING:
    from grassland.world import World


class Lion(Carnivore):
    def __init__(self, position: Vec2):
        super().__init__("Lion", position, (207, 157, 74), 120.0, 82.0, 22.0, 245.0)
        self.hunt_stamina_cost = 12.0

    def roar(self, world: "World") -> None:
        for animal in world.living_animals():
            if (
                animal.name == "Zebra"
                and isinstance(animal, Herbivore)
                and self.position.distance_to(animal.position) <= 180.0
            ):
                animal.panic_boost_timer = 5.0
        self.action_text = "roar"

    def yacha(self, target: "Carnivore | Herbivore", world: "World") -> None:
        self.attack(target, world)
        self.action_text = "yacha"
