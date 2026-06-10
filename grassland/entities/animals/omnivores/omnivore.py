# =============================================================================
# omnivore.py — 잡식동물 부모 (계획서 Omnivore)
# 고유 속성: diet_preference(0~1, 육식↔초식), aggression(위협 시 맞섬 정도)
# 고유 메서드: search_food(), eat()(오버라이딩), flee_or_fight()
# =============================================================================
import random

from grassland.entities.animals.animal import Animal
from grassland.entities.resources.carcass import Carcass


class Omnivore(Animal):
    def __init__(self, name, position, color, health, speed, power,
                 detect_range=105.0, radius=17.0):
        super().__init__(name, position, color, health, speed, power,
                         detect_range, radius=radius)
        self.diet_type = "omnivore"
        self.diet_preference = 0.5   # 0=초식 선호, 1=육식 선호
        self.aggression = 0.4        # 위협 시 도망 대신 맞설 확률 (0~1)
        self.forage_range = detect_range

    def update(self, world, dt):
        if not self.alive:
            return
        self.age += dt
        self.hunger = min(100.0, self.hunger + 1.3 * dt)   # 배고픔 증가
        self.thirst = min(100.0, self.thirst + 0.6 * dt)   # 갈증 증가
        self.recover_stamina(dt)
        # behave()가 행동을 처리하지 못했으면 배회
        if not self.behave(world, dt):
            self.wander(world, dt)

    def behave(self, world, dt):
        # 1순위: 포식자 감지 → 도망 또는 맞섬
        threat = world.nearest_predator(self, self.detect_range)
        if threat is not None:
            self.flee_or_fight(threat, world, dt)
            return True

        # 2순위: 갈증이 심하면 물 찾기
        if self.seek_water_if_needed(world):
            return True

        # 3순위: 배고프면 먹이 탐색
        return self.search_food(world, dt)

    def eat(self, food):
        if isinstance(food, Carcass):
            self.interaction_target = food
            self.action_text = "eat"
            if self._feed_ready():
                food.reduce_hunger(self)
                food.being_eaten_by = self
        else:
            super().eat(food)

    def search_food(self, world, dt):
        threshold = 20.0 if self.stamina < 25.0 else 58.0
        if self.hunger < threshold:
            return False
        if random.random() < self.aggression:
            prey = world.nearest_weak_or_prey(self, self.detect_range)
            if prey is not None:
                self.interaction_target = prey
                if self.distance_to(prey) <= self.radius + prey.radius + 8:
                    self.attack(prey, world)
                    self.lose_energy(7.0 * dt)
                else:
                    self.move_toward(prey.position, self.speed)
                    self.action_text = "hunt"
                return True
        carcass = world.nearest_carcass(self.position, self.food_range)
        plant = world.nearest_plant(self.position, self.food_range)
        if carcass is None and plant is None:
            return False
        if carcass is None:
            food = plant
        elif plant is None:
            food = carcass
        else:
            food = carcass if random.random() < self.diet_preference else plant
        self.interaction_target = food
        if self.distance_to(food) <= self.radius + food.radius + 8:
            self.eat(food)
            self.stop()
        else:
            self.move_toward(food.position, self.speed * 0.75)
            self.action_text = "search_food"
        return True

    def flee_or_fight(self, threat, world, dt):
        # aggression 확률 + 근거리일 때만 공격, 나머지는 도망
        if random.random() < self.aggression and self.distance_to(threat) < 42:
            self.attack(threat, world)
            self.lose_energy(7.0 * dt)
        else:
            self.evade(threat.position, self.speed * 1.15, dt)  # 속도 115%로 도주 (evade -5/s)
