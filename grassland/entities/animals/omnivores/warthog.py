from __future__ import annotations

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from grassland.world import World
    from grassland.entities.base import Entity

from grassland.entities.animals.omnivores.omnivore import Omnivore
from grassland.geometry import Vec2


class Warthog(Omnivore):
    def __init__(self, position: Vec2):
        super().__init__(
            name="Warthog",
            position=position,
            color=(121, 95, 70),
            health=72.0,
            speed=68.0,
            power=12.0,
            detect_range=165.0,
            radius=18.0,
        )
        self.diet_preference = 0.35
        self.aggression = 0.35
        self.tusk_power = 20.0
        self.burrow_location: Vec2 | None = None

    def dig(self, world: "World") -> Optional["Entity"]:
        food = world.nearest_plant(self.position)
        self.action_text = "dig"
        return food

    def burrow(self, world: "World") -> None:
        cave = world.nearest_terrain_type("Cave", self.position)
        if cave is not None:
            self.burrow_location = cave.position.copy()
            self.move_toward(cave.position, self.speed * 1.15)
            if cave.contains(self):
                self.is_hidden = True
                self.stop()
            self.action_text = "burrow"
            return

        self.burrow_location = self.position.copy()
        self.is_hidden = True
        self.stop()
        self.action_text = "burrow"

    def behave(self, world: "World", dt: float) -> bool:
        threat = world.nearest_predator(self, self.detect_range)
        if threat is not None:
            if (
                self.position.distance_to(threat.position) < 48.0
                and self.stamina > 18.0
            ):
                old_power = self.power
                self.power = self.tusk_power
                self.attack(threat, world)
                self.power = old_power
                self.lose_energy(10.0 * dt)
                self.action_text = "tusk"
            else:
                self.burrow(world)
                self.lose_energy(6.0 * dt)
            return True

        if self.seek_water_if_needed(world):
            return True

        if self.hunger > 52.0:
            food = self.dig(world)
            if food is not None:
                if (
                    self.position.distance_to(food.position)
                    <= self.radius + food.radius + 8
                ):
                    self.eat(food)
                    self.stop()
                else:
                    self.move_toward(food.position, self.speed * 0.72)
                return True

        return False
