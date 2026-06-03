from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from grassland.entities.animals.omnivores.omnivore import Omnivore
from grassland.entities.plants.grass import Grass
from grassland.entities.plants.plant import Plant
from grassland.entities.resources.carcass import Carcass
from grassland.geometry import Vec2

if TYPE_CHECKING:
    from grassland.world import World
    from grassland.entities.protocols import Consumable


class Meerkat(Omnivore):
    def __init__(self, position: Vec2):
        super().__init__(
            name="Meerkat",
            position=position,
            color=(198, 157, 93),
            health=42.0,
            speed=82.0,
            power=5.0,
            detect_range=185.0,
            radius=13.0,
        )
        self.diet_preference = 0.25
        self.aggression = 0.08
        self.is_sentinel = False
        self.sentinel_height = 0.0

    def stand(self) -> None:
        self.is_sentinel = True
        self.sentinel_height = 1.0
        self.stop()
        self.action_text = "stand"

    def eat_grass(self, grass: "Consumable") -> None:
        self.eat(grass)

    def behave(self, world: "World", dt: float) -> bool:
        threat = world.nearest_predator(
            self, self.detect_range * (1.25 if self.is_sentinel else 1.0)
        )
        if threat is not None:
            cave = world.nearest_terrain_type("Cave", self.position)
            if cave is not None:
                self.move_toward(cave.position, self.speed * 1.2)
                if cave.contains(self):
                    self.is_hidden = True
                    self.stop()
                    self.action_text = "hide"
                else:
                    self.action_text = "cave"
                self.lose_energy(5.0 * dt)
                return True
            self.flee_or_fight(threat, world, dt)
            return True

        if self.is_sentinel and self.hunger < 70.0 and self.thirst < 70.0:
            self.stand()
            return True

        self.is_sentinel = False
        self.sentinel_height = 0.0
        return super().behave(world, dt)

    def decide_food(self, world: "World") -> Optional[Carcass | Plant]:
        grass = world.nearest_alive(
            world.plants,
            self.position,
            lambda p: isinstance(p, Grass),
            self.forage_range,
        )
        if grass is not None:
            return grass
        return super().decide_food(world)
