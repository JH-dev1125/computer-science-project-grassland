# =============================================================================
# elephant.py — 코끼리 (계획서 Elephant, Herbivore 상속)
# 고유 속성: size_factor(클수록 접근 어려움), intimidation(포기 확률 영향)
# Fight=stomp()(포식자를 쫓아냄), Flight 거의 안 함
# =============================================================================
from grassland.entities.animals.herbivores.herbivore import Herbivore


class Elephant(Herbivore):
    def __init__(self, position):
        super().__init__("Elephant", position, (132, 132, 123),
                         health=165.0, speed=52.0, power=28.0, detect_range=220.0)
        self.radius = 28.0          # 큰 몸집 → 충돌·접근에 자동 반영
        self.size_factor = 1.8
        self.intimidation = 0.7

    def fight_or_flight(self, threat, world, dt):
        if self.distance_to(threat) < 70.0 * self.size_factor:
            self.stomp(threat, world)
        else:
            self.move_away_from(threat.position, self.flee_speed * 0.7)
            self.action_text = "flee"

    def stomp(self, threat, world):
        """짓밟기: 약간의 피해와 함께 포식자를 멀리 쫓아낸다(죽이기보다 격퇴)."""
        old_power, self.power = self.power, self.power * 0.4
        self.attack(threat, world)
        self.power = old_power
        threat.move_away_from(self.position, threat.speed * 1.6)
        self.action_text = "stomp"
