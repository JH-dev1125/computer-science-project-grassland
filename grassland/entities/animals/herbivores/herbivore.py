from __future__ import annotations
import random
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
        self.panic_range = detect_range
        self.base_panic_range = detect_range
        self.is_chased = False
        self.panic_boost_timer = 0.0
        self.reproduce_cooldown = 0.0
        self.flee_timer = 0.0
        self._last_threat_pos = None
        # 도주 운(luck): 매 1~3초마다 새로 굴려 실제 도주속도와 기동성을 살짝 변화시킨다.
        # 개체마다 다른 타이밍으로 굴러 떼가 엇갈리게 흩어지는 자연스러운 효과.
        self._escape_luck = 1.0
        self._escape_luck_timer = random.uniform(0.5, 2.0)

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
        else:
            self.panic_range = self.base_panic_range
        if self.reproduce_cooldown > 0:
            self.reproduce_cooldown = max(0.0, self.reproduce_cooldown - dt)
        if not self.is_chased and self.hunger < 40.0:
            self.heal(dt)
        if not self.is_chased:
            self.stress = max(0.0, self.stress - 5.0 * dt)
        if not self.behave(world, dt):
            self.wander(world, dt)

    def behave(self, world: "World", dt: float) -> bool:
        # 스트레스가 높을수록 포식자를 더 멀리서 감지한다(지속적인 경계 상태 반영).
        # stress=0 → 기본 범위, stress=100 → 최대 40px 추가. 이산적 배수가 아닌 연속 증가.
        stress_bonus = self.stress * 0.40
        effective_panic_range = self.panic_range + stress_bonus
        threat = world.nearest_predator(self, effective_panic_range)
        if threat is not None:
            self._last_threat_pos = threat.position.copy()
            self.flee_timer = 2.5
            if not self.is_chased:
                self.panic_boost_timer = 4.0
        self.flee_timer = max(0.0, self.flee_timer - dt)
        self.is_chased = self.flee_timer > 0.0
        if self.is_chased:
            self.stress = min(100.0, self.stress + 15.0 * dt)
            # 도주 운 타이머 갱신 — 1~3초마다 새 luck 값을 굴린다
            self._escape_luck_timer -= dt
            if self._escape_luck_timer <= 0.0:
                # 삼각분포: 대부분 보통(1.0 근처), 가끔 느리거나(0.65) 빠른(1.45) 도주
                self._escape_luck = random.triangular(0.65, 1.45, 1.0)
                self._escape_luck_timer = random.uniform(1.0, 3.0)
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
                self.evade(self._last_threat_pos, self.flee_speed * self._escape_luck, dt)
            return True
        return self.seek_water_if_needed(world) or self.search_food(world, dt)

    def search_food(self, world, dt):
        if self.hunger < 40.0:
            return False
        reach = None if self.hunger > 92.0 else self.food_range
        plant = world.nearest_plant(self.position, reach)
        if plant is None:
            return False
        self.interaction_target = plant
        if self.distance_to(plant) <= self.radius + plant.radius + 8:
            self.eat(plant)
            self.stop()
        else:
            self.move_toward(plant.position, self.speed * 0.7)
            self.action_text = "search_food"
        return True

    def can_hide_in_bush(self) -> bool:
        return False

    def heal(self, dt: float) -> None:
        # 스트레스가 높으면 회복이 느려진다(stress=0 → 4.0/s, stress=100 → 2.0/s).
        # 이산 임계값 없이 스트레스 수치에 비례해 연속적으로 감소.
        stress_penalty = self.stress * 0.020   # 최대 2.0 감소(스트레스 100)
        self.health = min(self.max_health, self.health + max(0.5, 4.0 - stress_penalty) * dt)

    @property
    def flee_speed(self):
        return self.speed * 1.25

    def fight_or_flight(
        self, threat: Animal, world: Optional["World"], dt: float
    ) -> None:
        health_ratio = self.health / self.max_health if self.max_health > 0 else 0.0
        if health_ratio > 0.7 and self.stamina > 60.0 and world is not None:
            self.attack(threat, world)
            self.lose_energy(7.0 * dt)
        else:
            # 도주 속도에 luck 배율 적용 — 운이 좋은 순간엔 탈출, 나쁘면 따라잡힌다
            # evade() 내부에서 -5/s 소모
            self.evade(threat.position, self.flee_speed * self._escape_luck, dt)

