from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from grassland.world import World
from grassland.entities.animals.animal import Animal
from pygame.math import Vector2


class Herbivore(Animal):
    def __init__(
        self,
        name: str,
        position: Vector2,
        color: tuple[int, int, int],
        health: float,
        speed: float,
        power: float,
        detect_range: float = 160.0,
    ):
        super().__init__(name, position, color, health, speed, power, detect_range)
        self.role = "herbivore"
        self.diet_type = "herbivore"
        self.flee_speed = speed * 1.25
        self.panic_range = detect_range
        self.base_panic_range = detect_range
        self.is_chased = False
        self.panic_boost_timer = 0.0
        self.reproduce_cooldown = 0.0

    def update(self, world: "World", dt: float) -> None:
        if not self.alive:
            return
        self.age += dt
        self.hunger = min(100.0, self.hunger + 2.4 * dt)
        self.thirst = min(100.0, self.thirst + 2.1 * dt)
        self.recover_stamina(dt)
        if self.panic_boost_timer > 0:
            self.panic_boost_timer = max(0.0, self.panic_boost_timer - dt)
            self.panic_range = self.base_panic_range * 2.0
            self.stamina_recovery_rate = 3.5
        else:
            self.panic_range = self.base_panic_range
            self.stamina_recovery_rate = 7.0
        if self.reproduce_cooldown > 0:
            self.reproduce_cooldown = max(0.0, self.reproduce_cooldown - dt)
        if not self.is_chased and self.hunger < 40.0:
            self.heal()
        if not self.is_chased:
            self.stress = max(0.0, self.stress - 5.0 * dt)
        if not self.behave(world, dt):
            self.wander(dt)

    def behave(self, world: "World", dt: float) -> bool:
        threat = world.nearest_predator(self, self.panic_range)
        if threat is not None and not self.is_chased:
            self.panic_boost_timer = 4.0
        self.is_chased = threat is not None
        if self.is_chased:
            self.stress = min(100.0, self.stress + 15.0 * dt)
        if threat is not None:
            bush = world.nearest_bush(self.position, 95.0)
            if bush is not None and self.can_hide_in_bush():
                self.move_toward(bush.position, self.flee_speed)
                if self.position.distance_to(bush.position) < bush.radius + self.radius:
                    bush.hide_entity(self)
                return True
            self.fight_or_flight(threat, world, dt)
            return True
        return self.seek_water_if_needed(world) or self.seek_plants_if_needed(world)

    def can_hide_in_bush(self) -> bool:
        return False

    def heal(self) -> None:
        self.health = min(self.max_health, self.health + 3.0)

    def fight_or_flight(
        self, threat: Animal, world: Optional["World"], dt: float
    ) -> None:
        health_ratio = self.health / self.max_health if self.max_health > 0 else 0.0
        if health_ratio > 0.7 and self.stamina > 60.0 and world is not None:
            self.attack(threat, world)
            self.lose_energy(10.0 * dt)
            self.action_text = "fight"
        else:
            self.move_away_from(threat.position, self.flee_speed)
            self.lose_energy(8.0 * dt)
            self.action_text = "flee"

