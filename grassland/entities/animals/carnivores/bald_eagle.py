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
#   예전엔 altitude 를 position.y 로부터 역산해 '항상 같은 높이로 보이도록'
#   흉내만 냈다 — 그래서 이 동물의 '실제' 높이는 사실상 지표면(땅)과 같았다.
#   지금은 altitude 를 이 동물이 직접 들고 있는 진짜 상태값으로 바꿔, 날 때는
#   FLY_ALTITUDE_MIN~MAX 사이를 자유로이 떠다니고(목표 고도를 가끔 새로 골라
#   서서히 다가감 — 상하 이동도 자유로움), 착지하면 0 으로 가라앉는다.
#   position 은 변함없이 '지면 위 투영점'(그림자 위치 = 사냥·채식 등 모든 거리
#   계산의 기준)으로 남고, gui 가 altitude 만큼 발밑을 들어 올려 그린다.
# =============================================================================
import random

from grassland.entities.animals.carnivores.carnivore import Carnivore

RISE_RATE = 70.0           # 떠오르거나 내려앉는 속도(px/초)
HORIZON_ZONE = 80.0        # 사체의 world y 가 이 값 이하면 '지평선 주위'로 간주한다
FLY_ALTITUDE_MIN = 70.0    # 비행 중 떠다니는 최저 고도 — 늘 이보다 위, 즉 지표면 위에 있다
FLY_ALTITUDE_MAX = 170.0   # 비행 중 떠다니는 최고 고도
WEAK_HEALTH_RATIO = 0.20   # 체력이 max_health 의 이 비율 미만이면 '빈사 상태'로 본다


class BaldEagle(Carnivore):
    def __init__(self, position):
        super().__init__("Bald_Eagle", position, (92, 82, 63),
                         health=58.0, speed=104.0, power=10.0, detect_range=300.0)
        self.radius = 14.0
        self.fly_speed = 150.0
        self.fly_time = 0.0
        self.is_flying = True
        self.action_text = "fly"
        # ── 고도(실제 상태값 — 늘 0보다 큰 값으로 시작해 '지표면 위'에서 산다) ──
        self.altitude = random.uniform(FLY_ALTITUDE_MIN, FLY_ALTITUDE_MAX)
        self._target_altitude = self.altitude
        self._altitude_timer = random.uniform(1.5, 4.0)
        # ── 빈사 상태 동물 사냥 ─────────────────────────────────────────
        self.hunt_target = None   # 노리고 있거나 방금 사냥한 '빈사 상태' 동물

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
        # 날 때: 목표 고도를 가끔 새로 뽑아(자유로운 상하 움직임) 그쪽으로 서서히
        # 다가간다 — FLY_ALTITUDE_MIN~MAX 사이를 벗어나지 않는다.
        # 착지하면 목표 고도 0 으로 서서히 가라앉는다. (position 은 그대로 — 그림자 위치)
        if self.is_flying:
            self._altitude_timer -= dt
            if self._altitude_timer <= 0.0:
                self._target_altitude = random.uniform(FLY_ALTITUDE_MIN, FLY_ALTITUDE_MAX)
                self._altitude_timer = random.uniform(1.5, 4.0)
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
        """탐지거리 안에서 체력이 WEAK_HEALTH_RATIO 미만으로 떨어진(=빈사 상태)
        가장 가까운 동물을 찾는다. 코끼리·같은 종(독수리끼리)은 사냥하지 않는다."""
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

    def hunt_weak_prey(self, world):
        """빈사 상태 동물을 발견했다면: 그 위치로 내려앉아 덮쳐 끝장내고, 자기 손으로
        만든 사체이므로 배고픔과 무관하게 그 자리에서 끝까지 먹는다(지평선 제약 없이).
        처리했으면 True."""
        target = self.hunt_target
        if target is None:
            target = self.find_weak_target(world)
            if target is None:
                return False
            self.hunt_target = target

        if target.alive:
            self.land()
            self.interaction_target = target
            if self.distance_to(target) <= self.radius + target.radius + 8:
                self.attack(target, world)
                self.stop()
            else:
                self.move_toward(target.position, self.fly_speed)
            self.action_text = "swoop"
            return True

        # 사냥감이 죽어 사체가 됨 — 자신이 직접 처치한 사체이니 배고픔과 무관하게
        # 끝까지(다 먹어 사라질 때까지) 먹는다.
        carcass = world.nearest_carcass(self.position)
        if carcass is None:
            self.hunt_target = None
            return False
        self.land()
        self.interaction_target = carcass
        if self.distance_to(carcass) <= self.radius + carcass.radius + 8:
            self.eat_carcass(carcass)
            self.stop()
        else:
            self.move_toward(carcass.position, self.speed * 0.8)
            self.action_text = "carcass"
        if not carcass.alive:
            self.hunt_target = None
        return True

    def behave(self, world, dt):
        # 1순위: 즉각적 위협 — 사자·코끼리 회피 (안전이 먹이보다 우선)
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
        # 2순위: 빈사 상태 동물을 탐지거리 안에서 발견하면 직접 덮쳐 사냥하고,
        # 생긴 사체까지 그 자리에서 먹는다.
        if self.hunt_weak_prey(world):
            return True
        # 3순위: 일반적인 배고픔 — 사체를 지평선 주위(world y 가 작은 쪽)에서
        # 발견했을 때만 내려앉아 먹는다. 그 밖의 모든 경우에는 fly() 가 기본 상태다.
        if self.hunger > 40.0:
            carcass = world.nearest_carcass(self.position)
            if carcass is not None and carcass.position.y <= HORIZON_ZONE:
                if self.distance_to(carcass) <= self.radius + carcass.radius + 8:
                    self.land()
                    self.eat_carcass(carcass)
                    self.stop()
                else:
                    self.fly()
                    self.move_toward(carcass.position, self.speed * 0.8)
                    self.action_text = "carcass"
                return True
        # 4순위: 기본 상태 — 상공 선회
        self.fly()
        return False
