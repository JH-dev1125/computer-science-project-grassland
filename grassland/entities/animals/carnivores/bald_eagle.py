# =============================================================================
# bald_eagle.py — 대머리 독수리 (계획서 Bald_eagle, Carnivore 상속)
# 고유 속성: is_flying, fly_speed, fly_time, altitude
# 고유 메서드: fly(), land()
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
#
#  [실행 흐름에서의 위치]
#    Carnivore 상속이지만 거의 다 오버라이드한다. update() 는 부모 호출 후 '고도'를 갱신하고,
#    behave() 우선순위는: ① 사자/코끼리 회피 → ② 물 → ③ 빈사 동물 급강하 사냥 →
#    ④ 지평선 근처 사체 → ⑤ 순찰 비행(절대 멈추지 않음).
# =============================================================================
import random

from pygame.math import Vector2

from grassland.entities.animals.carnivores.carnivore import Carnivore

# [문법] 모듈 수준 상수(클래스 밖) : 이 파일 전용 설정값들.
RISE_RATE = 90.0           # [변수] 떠오르거나 내려앉는 속도(px/초)
HORIZON_ZONE = 80.0        # [변수] 사체의 world y 가 이 값 이하면 '지평선 주위'로 간주
FLY_ALTITUDE_MIN = 70.0    # [변수] 비행 중 최저 고도
FLY_ALTITUDE_MAX = 200.0   # [변수] 비행 중 최고 고도
WEAK_HEALTH_RATIO = 0.20   # [변수] 체력이 이 비율 미만이면 '빈사 상태'(사냥 대상)


class BaldEagle(Carnivore):
    def __init__(self, position):
        super().__init__("Bald_Eagle", position, (92, 82, 63),
                         health=58.0, speed=122.0, power=10.0, detect_range=300.0)
        self.radius = 14.0             # [변수] 작은 충돌 크기
        self.thirst_limit = 88.0       # [변수] 물을 잘 안 찾음(높은 한계)
        self.food_range = 200.0        # [변수] 사체 탐지 — 고도에서 넓게 본다
        self.fly_speed = 188.0         # [변수] 비행 속도(가장 빠름)
        self.fly_time = 0.0
        self.is_flying = True          # [변수] 현재 날고 있는가(기본은 비행)
        self.action_text = "fly"
        # ── 고도(실제 상태값) ────────────────────────────────────────────
        self.altitude = random.uniform(FLY_ALTITUDE_MIN, FLY_ALTITUDE_MAX)  # [변수] 현재 고도
        self._target_altitude = self.altitude        # [변수] 천천히 다가갈 목표 고도
        self._altitude_timer = random.uniform(1.5, 4.0)  # [변수] 목표 고도를 새로 뽑을 때까지 시간
        # ── 빈사 상태 동물 사냥 ─────────────────────────────────────────
        self.hunt_target = None        # [변수] 현재 급강하 중인 빈사 사냥감
        self.hunt_stamina_cost = 5.0
        # ── 순찰 비행 (가만히 있지 않도록) ──────────────────────────────
        self._patrol_heading = random.uniform(0.0, 360.0)  # [변수] 순찰 방향(도)
        self._patrol_timer = random.uniform(1.0, 3.0)      # [변수] 다음 방향 전환까지 시간
        # 순찰 속도 벡터를 캐싱 — 방향 전환 시에만 다시 계산, 매 프레임 random 호출 제거
        _init_speed = self.fly_speed * random.uniform(0.55, 0.80)
        self._patrol_velocity = Vector2(1.0, 0.0).rotate(self._patrol_heading) * _init_speed

    def fly(self):
        """비행 상태로 전환."""
        self.is_flying = True
        self.action_text = "fly"

    def land(self):
        """착지 상태로 전환(고도가 0으로 내려감)."""
        self.is_flying = False
        self.action_text = "land"

    def update(self, world, dt):
        """부모(Carnivore.update) 처리 후 '고도'를 목표 쪽으로 서서히 움직인다."""
        # [←호출] world.update() 3단계.
        if not self.alive:
            return
        super().update(world, dt)      # [호출→] Carnivore.update(허기/갈증 + behave)
        # 날 때: 목표 고도를 가끔 새로 뽑아 서서히 다가간다. 착지하면 목표 0.
        if self.is_flying:
            self._altitude_timer -= dt
            if self._altitude_timer <= 0.0:
                self._target_altitude = random.uniform(FLY_ALTITUDE_MIN, FLY_ALTITUDE_MAX)
                self._altitude_timer = random.uniform(1.5, 4.5)
            target = self._target_altitude
        else:
            target = 0.0
        step = RISE_RATE * dt          # 이번 프레임에 오르내릴 수 있는 최대 고도
        if self.altitude < target:
            self.altitude = min(target, self.altitude + step)   # 목표까지 상승(넘지 않게)
        elif self.altitude > target:
            self.altitude = max(target, self.altitude - step)   # 목표까지 하강

    def find_weak_target(self, world):
        """탐지거리 안에서 빈사 상태인 가장 가까운 동물을 찾는다. 코끼리·독수리 제외."""
        target, nearest = None, None
        for animal in world.living_animals():
            if animal is self or animal.name in ("Bald_Eagle", "Elephant"):
                continue
            if animal.health > animal.max_health * WEAK_HEALTH_RATIO:
                continue                # 아직 빈사가 아니면 제외
            d = self.distance_to(animal)
            if d <= self.detect_range and (nearest is None or d < nearest):
                target, nearest = animal, d
        return target

    def hunt(self, prey, world, dt):
        """Carnivore.hunt() 확장 — 빈사 동물 추적·급강하·사체 섭취까지 일괄 처리.
        이동 속도는 fly_speed + acceleration 으로 부모의 acceleration 메커니즘을 사용."""
        if self.hunt_target is not prey:   # 새 먹이 → 급강하 시작 비용
            self.lose_energy(35.0)
        self.hunt_target = prey

        if prey.alive:
            if self.stamina <= 8.0:
                self.rest(dt)              # 지치면 휴식
                return
            self.land()                    # 사냥 시 내려꽂힘
            self.interaction_target = prey
            if self.distance_to(prey) <= self.radius + prey.radius + 8:
                was_alive = prey.alive
                self.attack(prey, world)
                if was_alive and not prey.alive:
                    self.hunt_target = None  # 다음 틱에서 search_food()가 사체 탐지
                    self.stop()
            else:
                self.move_toward(prey.position, self.fly_speed + self.acceleration)  # 급강하
            self.action_text = "swoop"
            self.lose_energy(self.hunt_stamina_cost * dt)
            return

        # 이미 죽어있으면 hunt_target 해제 → search_food()가 근처 사체 탐지
        self.hunt_target = None

    def behave(self, world, dt):
        """독수리 판단(Carnivore.behave 완전 오버라이드)."""
        # 1순위: 위협 회피(사자·코끼리)
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
        # 2순위: 갈증 해소
        if self.seek_water_if_needed(world):
            return True
        # 3순위: 빈사 동물 사냥 (이미 노린 게 있으면 그걸, 없으면 새로 찾기)
        # [문법] A or B : A 가 None(없음)이면 B 를 평가. hunt_target 우선, 없으면 find_weak_target.
        target = self.hunt_target or self.find_weak_target(world)
        if target is not None:
            self.hunt(target, world, dt)   # [호출→] hunt(급강하)
            return True
        # 4순위: 배고프면 지평선 근처 사체로 (HORIZON_ZONE 안에 있는 사체만 — 화면 위쪽)
        if self.hunger > 40.0:
            carcass = self.nearest_available_carcass(world, self.food_range)
            if carcass is not None and carcass.position.y <= HORIZON_ZONE:
                if self.distance_to(carcass) <= self.radius + carcass.radius + 8:
                    self.land()
                    self.eat(carcass)
                    self.stop()
                else:
                    self.fly()
                    self.move_toward(carcass.position, self.fly_speed)
                    self.action_text = "search_food"
                return True
        # 5순위: 순찰 비행 — 항상 움직이며 주기적으로 방향 전환(절대 멈추지 않음)
        self._patrol_timer -= dt
        if self._patrol_timer <= 0.0:
            self._patrol_heading += random.uniform(-90.0, 90.0)
            self._patrol_timer = random.uniform(1.5, 4.0)
            # 방향 전환 시에만 속도 벡터를 새로 계산 — 매 프레임 random 호출을 제거해
            # 속도가 프레임마다 들쭉날쭉하지 않고 일정하게 유지된다(애니메이션 안정성 ↑)
            new_speed = self.fly_speed * random.uniform(0.55, 0.80)
            self._patrol_velocity = Vector2(1.0, 0.0).rotate(self._patrol_heading) * new_speed
        self.fly()
        self.desired_velocity = self._patrol_velocity   # 캐싱된 순찰 속도로 이동
        self.action_text = "fly"
        return True
