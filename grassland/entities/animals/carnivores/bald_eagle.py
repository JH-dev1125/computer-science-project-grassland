# =============================================================================
# bald_eagle.py — 대머리 독수리 (계획서 Bald_eagle, Carnivore 상속)
# 고유 속성: is_flying, fly_speed, fly_time
# 고유 메서드: fly(), land(), eat_carcass()
# 분해자 역할: 늘 상공을 선회하며(생활의 약 80%), 지평선 부근에서 사체를 발견했을
#             때만 내려앉아 먹는다. 그 밖에는 fly() 가 이 동물의 기본 상태다.
# =============================================================================
from grassland.entities.animals.carnivores.carnivore import Carnivore

SKY_MARGIN = 24.0   # 날 때 지평선(HORIZON_Y) 위로 이만큼 띄워, 항상 하늘 영역에 보이게 한다
RISE_RATE = 70.0    # 떠오르거나 내려앉는 속도(px/초)
HORIZON_ZONE = 80.0  # 사체의 world y 가 이 값 이하면 '지평선 주위'로 간주한다


class BaldEagle(Carnivore):
    def __init__(self, position):
        super().__init__("Bald_Eagle", position, (92, 82, 63),
                         health=58.0, speed=104.0, power=10.0, detect_range=180.0)
        self.radius = 14.0
        self.fly_speed = 150.0
        self.fly_time = 0.0
        self.altitude = 0.0   # gui 가 이 값만큼 발밑을 들어 올려 그린다(그림자도 함께 그림)
        self.is_flying = True
        self.action_text = "fly"

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
        # 날면 서서히 떠오르고 착지하면 서서히 가라앉는다(화면 표시용 — 실제 위치는 그대로).
        # 떠 있는 동안은 화면상 항상 지평선 위(하늘)에 보이도록, 발밑(world y)이
        # 깊을수록 더 높이 띄운다 — 그러면 그려지는 위치가 지평선보다 SKY_MARGIN 만큼
        # 위로 일정하게 유지된다.
        target = self.position.y + SKY_MARGIN if self.is_flying else 0.0
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
        # 2순위: 배고픔 — 위협 없을 때만 사체에 내려앉음
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
        # 3순위: 기본 상태 — 상공 선회
        self.fly()
        return False

