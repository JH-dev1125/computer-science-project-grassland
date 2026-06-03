from __future__ import annotations

import random
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from grassland.world import World
    from grassland.entities.protocols import Consumable

from grassland.entities.animals.animal import Animal
from grassland.entities.plants.plant import Plant
from grassland.entities.resources.carcass import Carcass
from grassland.geometry import Vec2


class Omnivore(Animal):
    def __init__(
        self,
        name: str,
        position: Vec2,
        color: tuple[int, int, int],
        health: float,
        speed: float,
        power: float,
        detect_range: float = 150.0,
        radius: float = 17.0,
    ):
        super().__init__(
            name,
            position,
            color,
            health,
            speed,
            power,
            detect_range=detect_range,
            radius=radius,
        )
        self.role = "omnivore"
        self.diet_type = "omnivore"
        self.diet_preference = 0.5
        self.aggression = 0.4
        self.forage_range = detect_range

    def update(self, world: "World", dt: float) -> None:
        if not self.alive:
            return
        self.age += dt
        self.hunger = min(100.0, self.hunger + 2.6 * dt)
        self.thirst = min(100.0, self.thirst + 2.2 * dt)
        self.recover_stamina(dt)

        if not self.behave(world, dt):
            self.wander(dt)

    def behave(self, world: "World", dt: float) -> bool:
        threat = world.nearest_predator(self, self.detect_range)
        if threat is not None:
            self.flee_or_fight(threat, world, dt)
            return True
        if self.seek_water_if_needed(world):
            return True
        if self.hunger > 58.0:
            food = self.decide_food(world)
            if food is not None:
                if self.position.distance_to(food.position) <= self.radius + food.radius + 8:
                    self.eat(food)
                    self.stop()
                else:
                    self.move_toward(food.position, self.speed * 0.75)
                    self.action_text = "forage"
                return True
        return False

    def eat(self, food: "Consumable") -> None:
        if isinstance(food, Carcass):
            food.reduce_hunger(self)
            food.being_eaten_by = self
            self.action_text = "eat_carcass"
        else:
            super().eat(food)

    def decide_food(self, world: "World") -> Optional[Carcass | Plant]:
        carcass = world.nearest_carcass(self.position)
        plant = world.nearest_plant(self.position)

        if carcass is None:
            return plant
        if plant is None:
            return carcass

        return carcass if random.random() < self.diet_preference else plant

    def forage(self, world: "World") -> Optional[Carcass | Plant]:
        return self.decide_food(world)

    def flee_or_fight(self, threat: Animal, world: "World", dt: float) -> None:
        if random.random() < self.aggression and self.position.distance_to(threat.position) < 42:
            self.attack(threat, world)
        else:
            self.move_away_from(threat.position, self.speed * 1.15)
            self.action_text = "flee"
        self.lose_energy(6.0 * dt)
