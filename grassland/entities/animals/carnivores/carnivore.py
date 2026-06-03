from __future__ import annotations
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from grassland.world import World
    from grassland.entities.base import Entity

from grassland.entities.animals.animal import Animal
from grassland.geometry import Vec2


class Carnivore(Animal):
    def __init__(
        self,
        name: str,
        position: Vec2,
        color: tuple[int, int, int],
        health: float = 100.0,
        speed: float = 78.0,
        power: float = 18.0,
        detect_range: float = 230.0,
    ):
        super().__init__(
            name, position, color, health, speed, power, detect_range, radius=20
        )
        self.role = "carnivore"
        self.diet_type = "carnivore"
        self.stealth = 0.18
        self.acceleration = 34.0
        self.hunt_stamina_cost = 10.0

    def update(self, world: "World", dt: float) -> None:
        if not self.alive:
            return
        self.age += dt
        self.hunger = min(100.0, self.hunger + 3.0 * dt)
        self.thirst = min(100.0, self.thirst + 2.4 * dt)
        self.recover_stamina(dt)
        if not self.behave(world, dt):
            self.wander(dt)

    def behave(self, world: "World", dt: float) -> bool:
        if self.seek_water_if_needed(world):
            return True
        if self.hunger > 45.0:
            carcass = world.nearest_carcass(self.position)
            if carcass is not None:
                if (
                    self.position.distance_to(carcass.position)
                    <= self.radius + carcass.radius + 8
                ):
                    self.eat(carcass)
                    self.stop()
                else:
                    self.move_toward(carcass.position, self.speed * 0.75)
                    self.action_text = "carcass"
                return True
            prey = self.find_prey(world)
            if prey is not None:
                self.hunt(prey, world, dt)
                return True
        return False

    def eat(self, food: "Entity") -> None:
        if getattr(food, "name", "") == "Carcass":
            carcass: Any = food
            if hasattr(food, "reduce_hunger"):
                carcass.reduce_hunger(self)
            elif hasattr(food, "consume"):
                eaten = carcass.consume(22)
                self.hunger = max(0.0, self.hunger - eaten)
            if hasattr(food, "being_eaten_by"):
                carcass.being_eaten_by = self
            self.action_text = "eat_carcass"
        else:
            super().eat(food)

    def hunt(self, prey: Animal, world: "World", dt: float) -> None:
        if self.stamina <= 8.0:
            self.rest()
            return
        distance = self.position.distance_to(prey.position)
        if distance <= self.radius + prey.radius + 8:
            self.attack(prey, world)
            self.lose_energy(self.hunt_stamina_cost * dt)
            return
        self.move_toward(prey.position, self.speed + self.acceleration)
        self.lose_energy(self.hunt_stamina_cost * dt)
        self.action_text = "hunt"

    def hide(self) -> None:
        self.is_hidden = True
        self.action_text = "hide"

    def rest(self) -> None:
        self.stop()
        self.recover_stamina(0.8)
        self.action_text = "rest"

    def detect(self, target: Animal) -> bool:
        if getattr(target, "is_hidden", False):
            return self.position.distance_to(target.position) < self.detect_range * (
                1.0 - self.stealth
            )
        return self.position.distance_to(target.position) <= self.detect_range

    def find_prey(self, world: "World") -> Optional[Animal]:
        return world.nearest_prey_for(self, self.detect_range)
