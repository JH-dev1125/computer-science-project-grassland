from __future__ import annotations

from typing import Optional

from grassland.entities.animals.animal import Animal
from grassland.entities.resources.carcass import Carcass
from grassland.geometry import Vec2


class BaldEagle(Carnivore):
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
        super().__init__(name, position, color, health, speed, power, detect_range, radius=20)
        self.stealth = 0.18
        self.acceleration = 34.0
        self.hunt_stamina_cost = 10.0
        self.fly_time = 10.0
        self.is_flying = False
        self.fly_speed = 100.0

    def fly(self,world: object,dt: float) --> None:
        self.fly_time -= dt
        self.action_text = "fly"
        self.is_flying = True
        self.move_toward(Vec2(random.uniform(0, world.width), random.uniform(0, world.height)), self.fly_speed)
        self.lose_energy(1.0 * dt) # flying은 일반 이동보다 더 많은 에너지 소모
        if self.fly_time <= 0:
            self.land()
    def land(self) -> None:
        self.is_flying = False
        self.fly_time = 10.0
        self.action_text = "land"
    def eat(self, food: object) -> None:
        if isinstance(food, Carcass):
            food.reduce_hunger(self)
        else:
            super().eat(food)
        
    
