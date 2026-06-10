# =============================================================================
# gazelle.py — 가젤 (계획서 Gazelle, Herbivore 상속)
# 고유 속성: endurance(장거리 도주 지속력), zigzag_angle(방향 전환 각도)
# Fight 없음, Flight=zigzag() 로 포식자 acceleration 무력화
# =============================================================================
from grassland.entities.animals.herbivores.herbivore import Herbivore


class Gazelle(Herbivore):
    def __init__(self, position):
        super().__init__("Gazelle", position, (205, 166, 96),
                         health=52.0, speed=96.0, power=5.0, detect_range=140.0)
        self.thirst_limit = 56.0  # 가젤은 자주 물을 찾는다(가장 먼저 물가로)
        self.food_range = 80.0         # 풀 탐지 — 짧게 유지해 분산 유도(detect_range=140)
        self.endurance = 0.6      # 높을수록 도주 중 스태미나 소모↓
        self.zigzag_angle = 52.0  # 방향 전환 각도(도) — Vector2.rotate 는 '도' 단위
        self.agility = 9.0        # 가젤은 민첩 → 지그재그가 빠르게 반영된다

    def fight_or_flight(self, threat, world, dt):
        self.zigzag(threat, dt)
        self.lose_energy((1.0 - self.endurance) * 4.0 * dt)

    def zigzag(self, threat, dt):
        """좌우로 '번갈아' 크게 꺾어 달리는 지그재그 도주(가젤 특기). evade 에 강한 횡방향
        성분(lateral)과 짧은 전환 주기(period)를 줘, 관성으로 못 따라오는 포식자를 흔든다.
        zigzag_angle 이 클수록 더 예리하게 꺾여 따라오기 어렵게 된다(52° → lateral≈1.16)."""
        lateral = self.zigzag_angle / 45.0   # 45°=1.0, 52°≈1.16 — 각도가 직접 기동성에 반영됨
        self.evade(threat.position, self.flee_speed * self._escape_luck, dt,
                   lateral=lateral, period=0.4)
        self.action_text = "zigzag"
