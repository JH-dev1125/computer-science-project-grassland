# =============================================================================
# zebra.py — 얼룩말 (계획서 Zebra, Herbivore 상속)
# 고유 속성: kick_power, alert_radius
# Fight=kick(), Flight=flee()+AlertHerd()(무리에 경고 전파)
# =============================================================================
#
#  [실행 흐름에서의 위치]
#    Herbivore 상속. Herbivore.behave 가 위협 시 fight_or_flight 를 부르는데,
#    Zebra 는 이걸 오버라이드해 '코너에 몰리면 뒷발차기, 아니면 도주+무리 경고'로 만든다.
# =============================================================================
from grassland.entities.animals.herbivores.herbivore import Herbivore


class Zebra(Herbivore):
    def __init__(self, position):
        super().__init__("Zebra", position, (232, 232, 218),
                         health=78.0, speed=86.0, power=7.0, detect_range=100.0)
        self.thirst_limit = 64.0
        self.food_range = 90.0         # [변수] 풀 탐지 거리
        self.kick_power = 9.0      # [변수] 뒷발차기 위력(반격이 포식자를 즉사시키지 않게 하향)
        self.alert_radius = 220.0  # [변수] 도주 시 경고를 전파하는 반경

    def fight_or_flight(self, threat, world, dt):
        """Herbivore.fight_or_flight 오버라이드: 근접하면 차고, 아니면 도주+경고."""
        if self.distance_to(threat) < self.radius + threat.radius + 6:
            self.kick(threat, world)         # 코너에 몰리면 뒷발차기
        else:
            self.evade(threat.position, self.flee_speed, dt, lateral=0.8)  # 좌우로 틀며 도주
            self.alert_herd(world)           # [호출→] alert_herd(도망치며 무리에 경고)

    def kick(self, threat, world):
        """뒷발차기 반격 — 잠깐 공격력을 kick_power 로 바꿔 때린 뒤 원복."""
        self.lose_energy(30.0)
        # [문법] a, self.power = self.power, self.kick_power : 동시 대입.
        #        원래 power 를 old_power 에 백업하고 power 를 kick_power 로 교체한다.
        old_power, self.power = self.power, self.kick_power
        self.attack(threat, world)           # [호출→] Animal.attack (이때 power=kick_power)
        self.power = old_power               # 원래 공격력으로 되돌림
        self.action_text = "kick"

    def alert_herd(self, world):
        """alert_radius 내 다른 Zebra 를 패닉 상태로 만든다."""
        for animal in world.living_animals():
            if animal is not self and animal.name == "Zebra" \
                    and self.distance_to(animal) <= self.alert_radius:
                # [문법] max(기존, 3.0) : 이미 더 긴 경계가 걸려 있으면 줄이지 않는다.
                animal.panic_boost_timer = max(animal.panic_boost_timer, 3.0)
