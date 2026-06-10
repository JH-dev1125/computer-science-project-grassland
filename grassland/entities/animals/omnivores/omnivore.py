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
        if self.hunger > 58.0:
            food = self.decide_food(world)
            if food is not None:
                if self.distance_to(food) <= self.radius + food.radius + 8:
                    # 먹이에 충분히 가까우면 즉시 섭취
                    self.eat(food)
                    self.stop()
                else:
                    # 아직 멀면 천천히 접근 (속도 75%)
                    self.move_toward(food.position, self.speed * 0.75)
                    self.action_text = "forage"
                return True
        return False

    def eat(self, food):
        # 사체면 사체 전용 처리, 식물이면 Animal.eat() 위임
        if isinstance(food, Carcass):
            self.interaction_target = food
            self.action_text = "eat_carcass"
            # 쿨다운이 끝났을 때만 실제로 에너지 회복 (너무 빠른 연속 섭취 방지)
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
        # diet_preference가 높을수록 사체를 더 자주 선택
        return carcass if random.random() < self.diet_preference else plant

    def forage(self, world):
        # decide_food() 래퍼 (외부 호출용)
        return self.decide_food(world)

    def flee_or_fight(self, threat, world, dt):
        # aggression 확률 + 근거리일 때만 공격, 나머지는 도망
        if random.random() < self.aggression and self.distance_to(threat) < 42:
            self.attack(threat, world)
            self.action_text = "fight"
        else:
            self.evade(threat.position, self.speed * 1.15, dt)  # 속도 115%로 도주
