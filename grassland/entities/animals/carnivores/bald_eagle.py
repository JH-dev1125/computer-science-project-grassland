# =============================================================================
# bald_eagle.py — 대머리 독수리 (계획서 Bald_eagle, Carnivore 상속)
# 고유 속성: is_flying, fly_speed, fly_time, altitude
# 고유 메서드: fly(), land(), eat_carcass()
# 분해자 역할: 늘 상공을 선회하며(생활의 약 80%), 지평선 부근에서 사체를 발견했을
#             때만 내려앉아 먹는다. 그 밖에는 fly() 가 이 동물의 기본 상태다.
# 단, 빈사 상태(체력 20% 미만)의 동물을 탐지거리 안에서 발견하면 곧장 내리꽂혀
# 사냥하고, 그 자리에서 생긴 사체를 먹는다(지평선 제약 없이).
#
# [고도 모델 — altitude 는 '진짜' 상태값]
#   날 때는 FLY_ALTITUDE_MIN~MAX 사이를 자유로이 떠다니고(목표 고도를 가끔 새로
#   골라 서서히 다가감), 착지하면 0 으로 가라앉는다.
#   position 은 변함없이 '지면 위 투영점'(그림자 위치 = 거리 계산 기준)으로 남고,
#   gui 가 altitude 만큼 발밑을 들어 올려 그린다.
# =============================================================================
import random

from pygame.math import Vector2

from grassland.entities.animals.carnivores.carnivore import Carnivore

RISE_RATE = 90.0           # 떠오르거나 내려앉는 속도(px/초) — 빠를수록 민첩한 느낌
HORIZON_ZONE = 80.0        # 사체의 world y 가 이 값 이하면 '지평선 주위'로 간주한다
FLY_ALTITUDE_MIN = 70.0    # 비행 중 최저 고도
FLY_ALTITUDE_MAX = 200.0   # 비행 중 최고 고도 (원본 170→200 으로 범위 확대)
WEAK_HEALTH_RATIO = 0.20   # 체력이 max_health 의 이 비율 미만이면 '빈사 상태'로 본다


class BaldEagle(Carnivore):
    def __init__(self, position):
        super().__init__("Bald_Eagle", position, (92, 82, 63),
                         health=58.0, speed=122.0, power=10.0, detect_range=300.0)
        self.radius = 14.0
        self.thirst_limit = 88.0
        self.food_range = 200.0        # 사체 탐지 — 고도에서 넓게 본다(detect_range=300)
        self.fly_speed = 188.0
        self.fly_time = 0.0
        self.is_flying = True
        self.action_text = "fly"
        # ── 고도(실제 상태값) ────────────────────────────────────────────
        self.altitude = random.uniform(FLY_ALTITUDE_MIN, FLY_ALTITUDE_MAX)
        self._target_altitude = self.altitude
        self._altitude_timer = random.uniform(1.5, 4.0)
        # ── 빈사 상태 동물 사냥 ─────────────────────────────────────────
        self.hunt_target = None
        # ── 순찰 비행 (가만히 있지 않도록) ──────────────────────────────
        self._patrol_heading = random.uniform(0.0, 360.0)
        self._patrol_timer = random.uniform(1.0, 3.0)
        # 순찰 속도 벡터를 캐싱 — 방향 전환 시에만 다시 계산, 매 프레임 random 호출 제거
        _init_speed = self.fly_speed * random.uniform(0.55, 0.80)
        self._patrol_velocity = Vector2(1.0, 0.0).rotate(self._patrol_heading) * _init_speed

    def fly(self):
        self.is_flying = True
        self.action_text = "fly"

    def land(self):
        self.is_flying = False
        self.action_text = "land"

    def update(self, world, dt):
        if not self.alive:
            return
        super().update(world, dt)
        # 날 때: 목표 고도를 가끔 새로 뽑아 서서히 다가간다.
        # 착지하면 목표 고도 0 으로 가라앉는다.
        if self.is_flying:
            self._altitude_timer -= dt
            if self._altitude_timer <= 0.0:
                self._target_altitude = random.uniform(FLY_ALTITUDE_MIN, FLY_ALTITUDE_MAX)
                self._altitude_timer = random.uniform(1.5, 4.5)
            target = self._target_altitude
        else:
            target = 0.0
        step = RISE_RATE * dt
        if self.altitude < target:
            self.altitude = min(target, self.altitude + step)
        elif self.altitude > target:
            self.altitude = max(target, self.altitude - step)

    def eat_carcass(self, carcass):
        carcass.reduce_hunger(self)
        carcass.being_eaten_by = self
        self.action_text = "eat_carcass"

    def find_weak_target(self, world):
        """탐지거리 안에서 빈사 상태인 가장 가까운 동물을 찾는다. 코끼리·독수리 제외."""
        target, nearest = None, None
        for animal in world.living_animals():
            if animal is self or animal.name in ("Bald_Eagle", "Elephant"):
                continue
            if animal.health > animal.max_health * WEAK_HEALTH_RATIO:
                continue
            d = self.distance_to(animal)
            if d <= self.detect_range and (nearest is None or d < nearest):
                target, nearest = animal, d
        return target

    def hunt(self, prey, world, dt):
        """Carnivore.hunt() 확장 — 빈사 동물 추적·급강하·사체 섭취까지 일괄 처리.
        이동 속도는 fly_speed + acceleration 으로 부모의 acceleration 메커니즘을 사용."""
        self.hunt_target = prey

        if prey.alive:
            if self.stamina <= 8.0:
                self.rest()
                return
            self.land()
            self.interaction_target = prey
            if self.distance_to(prey) <= self.radius + prey.radius + 8:
                was_alive = prey.alive
                self.attack(prey, world)
                if was_alive and not prey.alive:
                    self.claim_hunted_carcass(world, prey)
                self.stop()
            else:
                self.move_toward(prey.position, self.fly_speed + self.acceleration)
            self.action_text = "swoop"
            self.lose_energy(self.hunt_stamina_cost * dt)
            return

        # 먹이가 죽었으면 생긴 사체를 찾아 먹는다
        if self.hunted_carcass is None:
            self.claim_hunted_carcass(world, prey)
        if self.feed_hunted_carcass(world):
            if self.hunted_carcass is None:
                self.hunt_target = None
            return
        carcass = self.nearest_available_carcass(world, self.food_range)
        if carcass is None:
            self.hunt_target = None
            return
        self.interaction_target = carcass
        if self.distance_to(carcass) <= self.radius + carcass.radius + 8:
            self.land()
            self.eat_carcass(carcass)
            self.stop()
        else:
            self.fly()
            self.move_toward(carcass.position, self.fly_speed)
            self.action_text = "carcass"
        if not carcass.alive:
            self.hunt_target = None

    def behave(self, world, dt):
        # 1순위: 위협 회피
        lion = world.nearest_named("Lion", self.position, 110.0)
        if lion is not None:
            self.fly()
            self.move_away_from(lion.position, self.fly_speed)
            return True
        elephant = world.nearest_named("Elephant", self.position, 110.0)
        if elephant is not None:
            self.fly()
            self.move_away_from(elephant.position, self.fly_speed)
            return True
        if self.feed_hunted_carcass(world):
            return True
        # 2순위: 빈사 동물 사냥
        target = self.hunt_target or self.find_weak_target(world)
        if target is not None:
            self.hunt(target, world, dt)
            return True
        # 3순위: 배고프면 지평선 근처 사체로
        if self.hunger > 40.0:
            carcass = self.nearest_available_carcass(world, self.food_range)
            if carcass is not None and carcass.position.y <= HORIZON_ZONE:
                if self.distance_to(carcass) <= self.radius + carcass.radius + 8:
                    self.land()
                    self.eat_carcass(carcass)
                    self.stop()
                else:
                    self.fly()
                    self.move_toward(carcass.position, self.fly_speed)
                    self.action_text = "carcass"
                return True
        # 4순위: 순찰 비행 — 항상 움직이며 주기적으로 방향 전환(절대 멈추지 않음)
        self._patrol_timer -= dt
        if self._patrol_timer <= 0.0:
            self._patrol_heading += random.uniform(-90.0, 90.0)
            self._patrol_timer = random.uniform(1.5, 4.0)
            # 방향 전환 시에만 속도 벡터를 새로 계산 — 매 프레임 random 호출을 제거해
            # 속도가 프레임마다 들쭉날쭉하지 않고 일정하게 유지된다(애니메이션 안정성 ↑)
            new_speed = self.fly_speed * random.uniform(0.55, 0.80)
            self._patrol_velocity = Vector2(1.0, 0.0).rotate(self._patrol_heading) * new_speed
        self.fly()
        self.desired_velocity = self._patrol_velocity
        self.action_text = "fly"
        return True
