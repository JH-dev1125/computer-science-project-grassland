# =============================================================================
# gazelle.py — 가젤 (계획서 Gazelle, Herbivore 상속)
# 고유 속성: endurance(장거리 도주 지속력), zigzag_angle(방향 전환 각도)
# Fight 없음, Flight=zigzag() 로 포식자 acceleration 무력화
# =============================================================================
import random

from grassland.entities.animals.herbivores.herbivore import Herbivore
from grassland.geometry import Vec2


class Gazelle(Herbivore):
    def __init__(self, position):
        super().__init__("Gazelle", position, (205, 166, 96),
                         health=52.0, speed=96.0, power=5.0, detect_range=205.0)
        self.endurance = 0.6      # 높을수록 도주 중 스태미나 소모↓
        self.zigzag_angle = 0.9   # 방향 전환 각도(라디안)

    def fight_or_flight(self, threat, world, dt):
        self.zigzag(threat)
        self.lose_energy((1.0 - self.endurance) * 4.0 * dt)

    def zigzag(self, threat):
        """도주 방향을 zigzag_angle 만큼 불규칙 회전 → 직선 추격 무력화."""
        away = (self.position - threat.position).normalized()
        angle = random.uniform(-self.zigzag_angle, self.zigzag_angle)
        cos_a, sin_a = __import__("math").cos(angle), __import__("math").sin(angle)
        turned = Vec2(away.x * cos_a - away.y * sin_a,
                      away.x * sin_a + away.y * cos_a)
        self.velocity = turned * self.flee_speed
        self.action_text = "zigzag"
