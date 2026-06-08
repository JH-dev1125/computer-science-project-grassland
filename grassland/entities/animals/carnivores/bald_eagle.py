# =============================================================================
# bald_eagle.py — 대머리 독수리 (계획서 Bald_eagle, Carnivore 상속)
# 고유 속성: is_flying, fly_speed, fly_time
# 고유 메서드: fly(), land(), eat_carcass()
# 분해자 역할: 늘 상공을 선회하며(생활의 약 80%), 지평선 부근에서 사체를 발견했을
#             때만 내려앉아 먹는다. 그 밖에는 fly() 가 이 동물의 기본 상태다.
# =============================================================================
import random

from pygame.math import Vector2

from grassland.entities.animals.carnivores.carnivore import Carnivore

SKY_MARGIN = 24.0   # 날 때 지평선(HORIZON_Y) 위로 이만큼 띄워, 항상 하늘 영역에 보이게 한다
RISE_RATE = 90.0    # 떠오르거나 내려앉는 속도(px/초)
HORIZON_ZONE = 80.0  # 사체의 world y 가 이 값 이하면 '지평선 주위'로 간주한다


class BaldEagle(Carnivore):
    def __init__(self, position):
        super().__init__("Bald_Eagle", position, (92, 82, 63),
                         health=58.0, speed=122.0, power=10.0, detect_range=180.0)
        self.radius = 14.0
        self.fly_speed = 188.0
        self.fly_time = 0.0
        self.altitude = 0.0   # gui 가 이 값만큼 발밑을 들어 올려 그린다(그림자도 함께 그림)
        self.is_flying = True
        self.action_text = "fly"
        self._alt_offset = random.uniform(30.0, 110.0)   # 현재 목표 고도 오프셋
        self._alt_timer = random.uniform(2.0, 6.0)        # 다음 고도 변경까지(초)
        self._patrol_heading = random.uniform(0.0, 360.0) # 순찰 방향(도)
        self._patrol_timer = random.uniform(1.0, 3.0)     # 다음 방향 전환까지(초)

    def fly(self):
        self.is_flying = True
        self.action_text = "fly"

    def land(self):
        self.is_flying = False
        self.action_text = "land"

    def _tick_altitude(self, dt):
        """주기적으로 목표 고도 오프셋을 랜덤하게 바꿔 다양한 고도로 비행."""
        self._alt_timer -= dt
        if self._alt_timer <= 0.0:
            self._alt_offset = random.uniform(20.0, 130.0)
            self._alt_timer = random.uniform(2.5, 8.0)

    def update(self, world, dt):
        if not self.alive:
            return
        super().update(world, dt)
        self._tick_altitude(dt)
        target = (self.position.y + SKY_MARGIN + self._alt_offset) if self.is_flying else 0.0
        step = RISE_RATE * dt
        if self.altitude < target:
            self.altitude = min(target, self.altitude + step)
        elif self.altitude > target:
            self.altitude = max(target, self.altitude - step)

    def eat_carcass(self, carcass):
        carcass.reduce_hunger(self)
        carcass.being_eaten_by = self
        self.action_text = "eat_carcass"

    def behave(self, world, dt):
        # 사체를 지평선 주위(world y 가 작은 쪽)에서 발견했을 때만 내려앉아 먹는다.
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
        # 근처에 사자·코끼리가 있으면 회피 비행
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
        # 기본 순찰 비행: 항상 움직이며 주기적으로 방향 전환(절대 멈추지 않음)
        self._patrol_timer -= dt
        if self._patrol_timer <= 0.0:
            self._patrol_heading += random.uniform(-90.0, 90.0)
            self._patrol_timer = random.uniform(1.5, 4.0)
        self.fly()
        direction = Vector2(1.0, 0.0).rotate(self._patrol_heading)
        self.desired_velocity = direction * self.fly_speed * random.uniform(0.55, 0.80)
        self.action_text = "fly"
        return True
