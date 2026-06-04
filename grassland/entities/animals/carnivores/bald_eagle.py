# =============================================================================
# bald_eagle.py — 대머리 독수리 (계획서 Bald_eagle, Carnivore 상속)
# 고유 속성: is_flying, fly_speed, fly_time
# 고유 메서드: fly(), land(), eat_carcass()
# 분해자 역할: 사체를 먹되, 사자가 가까우면 날아서 피한다.
# =============================================================================
from grassland.entities.animals.carnivores.carnivore import Carnivore


class BaldEagle(Carnivore):
    def __init__(self, position):
        super().__init__("Bald_Eagle", position, (92, 82, 63),
                         health=58.0, speed=104.0, power=10.0, detect_range=260.0)
        self.radius = 14.0
        self.is_flying = False
        self.fly_speed = 150.0
        self.fly_time = 0.0

    def fly(self):
        self.is_flying = True
        self.action_text = "fly"

    def land(self):
        self.is_flying = False

    def eat_carcass(self, carcass):
        carcass.reduce_hunger(self)
        carcass.being_eaten_by = self
        self.action_text = "eat_carcass"

    def behave(self, world, dt):
        # 근처에 사자가 있으면 회피 비행
        lion = world.nearest_named("Lion", self.position, 110.0)
        if lion is not None:
            self.fly()
            self.move_away_from(lion.position, self.fly_speed)
            return True
        self.land()
        if self.hunger > 40.0:
            carcass = world.nearest_carcass(self.position)
            if carcass is not None:
                if self.distance_to(carcass) <= self.radius + carcass.radius + 8:
                    self.eat_carcass(carcass)
                    self.stop()
                else:
                    self.move_toward(carcass.position, self.speed * 0.8)
                    self.action_text = "carcass"
                return True
        return False
