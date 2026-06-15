# =============================================================================
# gazelle.py — 가젤 (계획서 Gazelle, Herbivore 상속)
# 고유 속성: endurance(장거리 도주 지속력), zigzag_angle(방향 전환 각도)
# Fight 없음, Flight=zigzag() 로 포식자 acceleration 무력화
# =============================================================================
#
#  [실행 흐름에서의 위치]
#    Herbivore 상속. fight_or_flight 를 오버라이드해 '맞서지 않고 무조건 지그재그 도주'한다.
#    가장 빠르지만 가장 약한 종이라 회피 기동이 유일한 생존 수단이다.
# =============================================================================
from grassland.entities.animals.herbivores.herbivore import Herbivore


class Gazelle(Herbivore):
    def __init__(self, position):
        super().__init__("Gazelle", position, (205, 166, 96),
                         health=52.0, speed=96.0, power=5.0, detect_range=110.0)
        self.thirst_limit = 56.0  # [변수] 가젤은 자주 물을 찾는다(가장 먼저 물가로)
        self.food_range = 80.0         # [변수] 풀 탐지 — 짧게 유지해 분산 유도
        self.endurance = 0.6      # [변수] 높을수록 도주 중 스태미나 소모↓(연출/확장용)
        self.zigzag_angle = 52.0  # [변수] 방향 전환 각도(도) — 클수록 예리하게 꺾음
        self.agility = 9.0        # [변수] 가젤은 민첩 → 지그재그가 빠르게 반영된다(기본 6보다 큼)

    def fight_or_flight(self, threat, world, dt):
        """Herbivore.fight_or_flight 오버라이드: 항상 지그재그 도주."""
        self.zigzag(threat, dt)

    def zigzag(self, threat, dt):
        """좌우로 '번갈아' 크게 꺾어 달리는 지그재그 도주(가젤 특기). evade 에 강한 횡방향
        성분(lateral)과 짧은 전환 주기(period)를 줘, 관성으로 못 따라오는 포식자를 흔든다.
        zigzag_angle 이 클수록 더 예리하게 꺾여 따라오기 어렵게 된다(52° → lateral≈1.16)."""
        # [변수] lateral : 횡방향(좌우) 세기. 각도를 45로 나눠 evade 의 lateral 인자로 전달.
        lateral = self.zigzag_angle / 45.0   # 45°=1.0, 52°≈1.16 — 각도가 직접 기동성에 반영됨
        self.evade(threat.position, self.flee_speed * self._escape_luck, dt,
                   lateral=lateral, period=0.4)   # [호출→] Animal.evade(짧은 주기로 격하게 꺾음)
        self.lose_energy(13.0 * dt)   # evade -5/s + 여기 -13/s = 합계 -18/s (격한 기동의 큰 소모)
        self.action_text = "zigzag"
