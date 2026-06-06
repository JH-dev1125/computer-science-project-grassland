# =============================================================================
# gazelle.py — 가젤 (계획서 Gazelle, Herbivore 상속)
# 고유 속성: endurance(장거리 도주 지속력), zigzag_angle(방향 전환 각도)
# Fight 없음, Flight=zigzag() 로 포식자 acceleration 무력화
# =============================================================================
import random

from pygame.math import Vector2

from grassland.entities.animals.herbivores.herbivore import Herbivore


class Gazelle(Herbivore):
    def __init__(self, position):
        super().__init__("Gazelle", position, (205, 166, 96),
                         health=52.0, speed=96.0, power=5.0, detect_range=205.0)
        self.endurance = 0.6      # 높을수록 도주 중 스태미나 소모↓
        self.zigzag_angle = 52.0  # 방향 전환 각도(도) — Vector2.rotate 는 '도' 단위
        self.agility = 9.0        # 가젤은 민첩 → 지그재그가 빠르게 반영된다

    def fight_or_flight(self, threat, world, dt):
        self.zigzag(threat)
        self.lose_energy((1.0 - self.endurance) * 4.0 * dt)

    def zigzag(self, threat):
        """도주 방향을 zigzag_angle 만큼 불규칙 회전 → 직선 추격 무력화.
        Vector2.rotate 로 멀어지는 방향을 좌우로 흔들어 준다."""
        away = self.position - threat.position
        if away.length_squared() < 1e-6:
            away = Vector2(1.0, 0.0)
        turned = away.normalize().rotate(
            random.uniform(-self.zigzag_angle, self.zigzag_angle))
        # 지향 속도만 설정 — 실제 가감속은 physics 의 steering 이 부드럽게 처리
        self.desired_velocity = turned * self.flee_speed
        self.action_text = "zigzag"
