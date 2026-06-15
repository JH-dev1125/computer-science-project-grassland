# =============================================================================
# omnivore.py — 잡식동물 부모 (계획서 Omnivore)
# 고유 속성: diet_preference(0~1, 육식↔초식), aggression(위협 시 맞섬 정도)
# 고유 메서드: search_food(), eat()(오버라이딩), flee_or_fight()
# =============================================================================
#
#  [실행 흐름에서의 위치]
#    Meerkat/Warthog 의 부모. world.update() 3단계에서 omnivore.update() 호출.
#    behave() 우선순위: ① 포식자 → 도망/맞섬  ② 물  ③ 먹이(약한 사냥감/사체/풀).
#    먹이 선택은 diet_preference(육식↔초식 선호)와 aggression(공격성) 확률로 갈린다.
# =============================================================================
import random

from grassland.entities.animals.animal import Animal     # 부모(공통 AI)
from grassland.entities.resources.carcass import Carcass  # '사체' 판별용


class Omnivore(Animal):
    def __init__(self, name, position, color, health, speed, power,
                 detect_range=105.0, radius=17.0):
        super().__init__(name, position, color, health, speed, power,
                         detect_range, radius=radius)
        self.diet_type = "omnivore"
        self.diet_preference = 0.5   # [변수] 0=초식 선호, 1=육식 선호 (사체 vs 풀 선택 확률)
        self.aggression = 0.4        # [변수] 위협 시 도망 대신 맞설 확률 (0~1)
        self.forage_range = detect_range   # [변수] 먹이 채집 범위(현재 거의 detect_range 와 동일)

    def update(self, world, dt):
        """잡식 매 프레임 진입점(Animal.update 오버라이드 — 허기/갈증 증가 추가)."""
        # [←호출] world.update() 3단계.
        if not self.alive:
            return
        self.age += dt
        self.hunger = min(100.0, self.hunger + 1.3 * dt)   # 배고픔 증가
        self.thirst = min(100.0, self.thirst + 0.6 * dt)   # 갈증 증가
        self.recover_stamina(dt)
        # behave()가 행동을 처리하지 못했으면 배회
        if not self.behave(world, dt):     # [호출→] behave
            self.wander(world, dt)

    def behave(self, world, dt):
        """잡식 판단 순서. (Meerkat/Warthog 이 더 정교하게 오버라이드)"""
        # 1순위: 포식자 감지 → 도망 또는 맞섬
        threat = world.nearest_predator(self, self.detect_range)   # [호출→] World.nearest_predator
        if threat is not None:
            self.flee_or_fight(threat, world, dt)   # [호출→] flee_or_fight
            return True

        # 2순위: 갈증이 심하면 물 찾기
        if self.seek_water_if_needed(world):
            return True

        # 3순위: 배고프면 먹이 탐색
        return self.search_food(world, dt)          # [호출→] search_food

    def eat(self, food):
        """사체면 being_eaten_by 표시, 그 외엔 부모 eat. (Animal.eat 오버라이드)"""
        if isinstance(food, Carcass):
            self.interaction_target = food
            self.action_text = "eat"
            if self._feed_ready():
                food.reduce_hunger(self)
                food.being_eaten_by = self    # '내가 먹는 중' 표시
        else:
            super().eat(food)

    def search_food(self, world, dt):
        """배고프면 약한 사냥감/사체/풀을 골라 먹는다."""
        threshold = 20.0 if self.stamina < 25.0 else 58.0
        if self.hunger < threshold:
            self._committed_food = None
            return False
        # committed target 유지 (먹잇감 공격은 random gate라 커밋하지 않음)
        if self._food_valid(self._committed_food):
            food = self._committed_food
            self.interaction_target = food
            if self.distance_to(food) <= self.radius + food.radius + 8:
                self.eat(food)
                self.stop()
            else:
                self.move_toward(food.position, self.speed * 0.75)
                self.action_text = "search_food"
            return True
        self._committed_food = None
        # [문법] random.random() < aggression : aggression 확률로 '공격적 사냥'을 시도.
        if random.random() < self.aggression:
            prey = world.nearest_weak_or_prey(self, self.detect_range)   # 약한 적/사냥감
            if prey is not None:
                self.interaction_target = prey
                if self.distance_to(prey) <= self.radius + prey.radius + 8:
                    self.attack(prey, world)
                    self.lose_energy(7.0 * dt)
                else:
                    self.move_toward(prey.position, self.speed)
                    self.action_text = "hunt"
                return True
        # 공격 안 했으면 사체/풀 중 선택
        carcass = world.nearest_carcass(self.position, self.food_range)
        plant = world.nearest_plant(self.position, self.food_range)
        if carcass is None and plant is None:
            return False
        if carcass is None:
            food = plant                  # 사체 없으면 풀
        elif plant is None:
            food = carcass                # 풀 없으면 사체
        else:
            # 둘 다 있으면 diet_preference 확률로 사체(육식 선호)/풀 선택
            food = carcass if random.random() < self.diet_preference else plant
        self._committed_food = food
        self.interaction_target = food
        if self.distance_to(food) <= self.radius + food.radius + 8:
            self.eat(food)
            self.stop()
        else:
            self.move_toward(food.position, self.speed * 0.75)
            self.action_text = "search_food"
        return True

    def flee_or_fight(self, threat, world, dt):
        """위협 대응: 공격성·근거리면 맞서고, 아니면 도망."""
        # aggression 확률 + 근거리일 때만 공격, 나머지는 도망
        if random.random() < self.aggression and self.distance_to(threat) < 42:
            self.attack(threat, world)
            self.lose_energy(7.0 * dt)
        else:
            self.evade(threat.position, self.speed * 1.15, dt)  # 속도 115%로 도주 (evade -5/s)
