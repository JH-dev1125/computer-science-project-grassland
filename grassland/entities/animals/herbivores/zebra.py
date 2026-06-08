# =============================================================================
# zebra.py — 얼룩말 (계획서 Zebra, Herbivore 상속)
# 고유 속성: kick_power, alert_radius
# Fight=kick(), Flight=flee()+AlertHerd()(무리에 경고 전파)
# =============================================================================
from grassland.entities.animals.herbivores.herbivore import Herbivore


class Zebra(Herbivore):
    def __init__(self, position):
        super().__init__("Zebra", position, (232, 232, 218),
                         health=78.0, speed=86.0, power=7.0, detect_range=185.0)
        self.kick_power = 9.0      # 뒷발차기(반격이 포식자를 즉사시키지 않게 하향)
        self.alert_radius = 220.0  # 경고 전파 반경

    def fight_or_flight(self, threat, world, dt):
        if self.distance_to(threat) < self.radius + threat.radius + 6:
            self.kick(threat, world)         # 코너에 몰리면 뒷발차기
        else:
            self.move_away_from(threat.position, self.flee_speed)
            self.alert_herd(world)           # 도망치며 무리에 경고
            self.action_text = "flee"

    def kick(self, threat, world):
        old_power, self.power = self.power, self.kick_power
        self.attack(threat, world)
        self.power = old_power
        self.action_text = "kick"

    def alert_herd(self, world):
        """alert_radius 내 다른 Zebra 를 패닉 상태로 만든다."""
        for animal in world.living_animals():
            if animal is not self and animal.name == "Zebra" \
                    and self.distance_to(animal) <= self.alert_radius:
                animal.panic_boost_timer = max(animal.panic_boost_timer, 3.0)
