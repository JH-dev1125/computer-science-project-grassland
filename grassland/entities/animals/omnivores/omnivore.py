# =============================================================================
# omnivore.py — 잡식동물 부모 (계획서 Omnivore)
# 고유 속성: diet_preference(0~1, 육식↔초식), aggression(위협 시 맞섬 정도)
# 고유 메서드: forage(), decide_food(), eat()(오버라이딩), flee_or_fight()
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
        self.diet_preference = 0.5   # 1에 가까울수록 육식 선호
        self.aggression = 0.4        # 위협 시 도망 대신 맞설 확률

    def update(self, world, dt):
        if not self.alive:
            return
        self.age += dt
        self.hunger = min(100.0, self.hunger + 1.3 * dt)
        self.thirst = min(100.0, self.thirst + 0.6 * dt)
        self.recover_stamina(dt)
        if not self.behave(world, dt):
            self.wander(world, dt)

    def behave(self, world, dt):
        threat = world.nearest_predator(self, self.detect_range)
        if threat is not None:
            self.flee_or_fight(threat, world, dt)
            return True
        if self.seek_water_if_needed(world):
            return True
        if self.hunger > 40.0:
            food = self.decide_food(world)
            if food is not None:
                if self.distance_to(food) <= self.radius + food.radius + 8:
                    self.eat(food)
                    self.stop()
                else:
                    self.move_toward(food.position, self.speed * 0.75)
                    self.action_text = "forage"
                return True
            if self.hunger >= self.HUNGER_SEARCH_LEVEL:
                return self.search_for_food(world, "search_food")
        return False

    def eat(self, food):
        if isinstance(food, Carcass):
            self.interaction_target = food
            self.action_text = "eat_carcass"
            if self._feed_ready():
                food.reduce_hunger(self)
                food.being_eaten_by = self
        else:
            super().eat(food)

    def decide_food(self, world):
        """diet_preference 에 따라 '먹이 탐지 거리(food_range)' 안의 사체/식물을 고른다."""
        carcass = world.nearest_carcass(self.position, self.food_range)
        plant = world.nearest_plant(self.position, self.food_range)
        if carcass is None:
            return plant
        if plant is None:
            return carcass
        return carcass if random.random() < self.diet_preference else plant

    def forage(self, world):
        """먹이 감지 범위 안에 없으면 범위를 늘리지 않고 이동 탐색한다."""
        return self.decide_food(world)

    def flee_or_fight(self, threat, world, dt):
        if random.random() < self.aggression and self.distance_to(threat) < 42:
            self.attack(threat, world)
            self.action_text = "fight"
        else:
            self.evade(threat.position, self.speed * 1.15, dt)
