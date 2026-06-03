from __future__ import annotations

import random
from abc import abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from grassland.world import World
    from grassland.entities.protocols import Consumable, Drinkable

from grassland.entities.base import Entity
from grassland.geometry import Vec2, random_unit_vector


# 8.0 이 여윳값의 최소 단위
class Animal(Entity):
    def __init__(
        self,
        name: str,
        position: Vec2,
        color: tuple[int, int, int],
        health: float,
        speed: float,
        power: float,
        detect_range: float,
        radius: float = 18,
    ):
        super().__init__(name=name, position=position, radius=radius, color=color)
        self.health = health
        self.max_health = health
        self.speed = speed
        self.power = power
        self.hunger = random.uniform(12.0, 42.0)
        self.thirst = random.uniform(12.0, 42.0)
        self.is_sleeping = False
        self.stamina = 100.0
        self.stamina_recovery_rate = 7.0
        self.stress = 0.0
        self.detect_range = detect_range
        self.is_hidden = False
        self.age = 0.0
        self.kind = "animal"
        self.diet_type: str = ""  # 서브클래스에서 "herbivore" / "carnivore" / "omnivore" 로 설정
        self.decision_timer = random.uniform(0.2, 1.4)
        self._carcass_spawned = False

    def move(self, direction: Vec2) -> None:
        self.velocity = (
            direction.normalized() * self.speed
        )  # normalized -> 물리에서 정규화랑 똑같)

    def eat(self, food: "Consumable") -> None:
        eaten = food.consume(14)
        self.hunger = max(0.0, self.hunger - eaten)
        self.action_text = "eat"

    def drink(self, source: "Drinkable") -> None:
        source.reduce_thirst(self)

    def sleep(
        self,
    ) -> None:  # -> 는 Type을 지정해주는 도구, 이를 위해 __future__ 불러옴
        self.is_sleeping = True
        self.action_text = "sleep"

    def wake_up(self) -> None:
        self.is_sleeping = False

    def lose_energy(self, amount: float) -> None:
        self.stamina = max(0.0, self.stamina - amount)  # 스태미나는 최솟값이 0

    def die(self, world: Optional["World"] = None) -> None:
        if not self.alive:
            return
        self.alive = False
        self.stop()
        self.action_text = "dead"
        if world is not None and not self._carcass_spawned:
            self._carcass_spawned = True
            world.spawn_carcass(self)  # 죽으면 carcass(시체 생성)

    def attack(self, target: "Animal", world: "World") -> None:
        if not target.alive:
            return
        target.health -= self.power
        target.stress = min(100.0, target.stress + 8.0)
        self.action_text = "attack"
        if target.health <= 0:
            target.die(world)

    def couple(self, one: "Animal", other: "Animal") -> bool:
        if one.alive and other.alive:
            return bool(round(random.uniform(0, 1)))
        return False

    def recover_stamina(self, dt: float) -> None:
        self.stamina = min(
            100.0, self.stamina + self.stamina_recovery_rate * dt
        )  # 스태미나 하한값 100.0

    def distant_to(self, target: "Entity") -> float:
        return self.distance_to(target)

    def seek_water_if_needed(self, world: "World") -> bool:
        if self.thirst < 58.0:
            return False  # 목 안마르면 굳이 시행 안함
        water = world.nearest_water(self.position)
        if water is None:  # No 물 -> 그냥 False 리턴하기
            return False
        if self.position.distance_to(water.position) <= self.radius + water.radius + 8:
            self.drink(water)
            self.stop()
        else:
            self.move_toward(water.position, self.speed * 0.85)
            self.action_text = "water"  # 물 찾을때까지 water.position 방향으로 이동하기
        return True

    def seek_plants_if_needed(self, world: "World") -> bool:
        if self.hunger < 62.0:
            return False  # 충분히 배부르면 굳이 안함
        plant = world.nearest_plant(self.position)
        if plant is None:
            return False
        if self.position.distance_to(plant.position) <= self.radius + plant.radius + 8:
            self.eat(plant)
            self.stop()
        else:
            self.move_toward(plant.position, self.speed * 0.7)
            self.action_text = (
                "풀 먹으러 가는 중"  # 풀 찾을 때까지 plant.position 방향으로 이동하기
            )
        return True

    def wander(self, dt: float) -> None:
        self.decision_timer -= dt
        if self.decision_timer > 0:
            return
        self.decision_timer = random.uniform(0.8, 2.2)
        if random.random() < 0.22:
            self.stop()
            self.action_text = "watch"
            return
        self.velocity = random_unit_vector() * random.uniform(
            self.speed * 0.18, self.speed * 0.45
        )
        self.action_text = "move"

    @abstractmethod
    def behave(self, world: "World", dt: float) -> bool:
        """매 틱 동물의 의사결정 로직. 행동을 취했으면 True, 아무것도 안 했으면 False."""
        ...
