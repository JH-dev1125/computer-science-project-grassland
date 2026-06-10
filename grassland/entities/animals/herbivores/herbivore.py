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
        detect_range: float = 110.0,
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
        self.flee_timer = 0.0
        self._last_threat_pos = None

    def update(self, world: "World", dt: float) -> None:
        if not self.alive:
            return
        self.age += dt
        self.hunger = min(100.0, self.hunger + 1.2 * dt)
        self.thirst = min(100.0, self.thirst + 0.55 * dt)
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
            self.heal(dt)
        if not self.is_chased:
            self.stress = max(0.0, self.stress - 5.0 * dt)
        if not self.behave(world, dt):
            self.wander(world, dt)

    def behave(self, world: "World", dt: float) -> bool:
        threat = world.nearest_predator(self, self.panic_range)
        if threat is not None:
            self._last_threat_pos = threat.position.copy()
            self.flee_timer = 2.5
            if not self.is_chased:
                self.panic_boost_timer = 4.0
        self.flee_timer = max(0.0, self.flee_timer - dt)
        self.is_chased = self.flee_timer > 0.0
        if self.is_chased:
            self.stress = min(100.0, self.stress + 15.0 * dt)
            if threat is not None:
                self.interaction_target = threat
                bush = world.nearest_bush(self.position, 95.0)
                if bush is not None and self.can_hide_in_bush():
                    self.move_toward(bush.position, self.flee_speed)
                    if self.position.distance_to(bush.position) < bush.radius + self.radius:
                        bush.hide_entity(self)
                    return True
                self.fight_or_flight(threat, world, dt)
            else:
                self.interaction_target = None
                self.evade(self._last_threat_pos, self.flee_speed, dt)
            return True
        return self.seek_water_if_needed(world) or self.seek_plants_if_needed(world)

    def can_hide_in_bush(self) -> bool:
        return False

    def heal(self, dt: float) -> None:
        # 초당 회복(예전엔 프레임당 +3 = 초당 180 으로 비정상적으로 빨랐다)
        self.health = min(self.max_health, self.health + 4.0 * dt)

    def fight_or_flight(
        self, threat: Animal, world: Optional["World"], dt: float
    ) -> None:
        health_ratio = self.health / self.max_health if self.max_health > 0 else 0.0
        if health_ratio > 0.7 and self.stamina > 60.0 and world is not None:
            self.attack(threat, world)
            self.lose_energy(10.0 * dt)
            self.action_text = "fight"
        else:
            self.evade(threat.position, self.flee_speed, dt)
            self.lose_energy(8.0 * dt)

