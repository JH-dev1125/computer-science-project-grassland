# =============================================================================
# herbivore.py — 피식자 부모 (계획서 Herbivore)
# 고유 속성: flee_speed, panic_range, is_chased
# 고유 메서드: heal(), FightOrFlight()(둘 중 하나 선택) → fight_or_flight()
# =============================================================================
from grassland.entities.animals.animal import Animal


class Herbivore(Animal):
    def __init__(self, name, position, color, health, speed, power,
                 detect_range=160.0):
        super().__init__(name, position, color, health, speed, power, detect_range)
        self.diet_type = "herbivore"
        self.flee_speed = speed * 1.25
        self.panic_range = detect_range
        self.base_panic_range = detect_range
        self.is_chased = False
        self.panic_boost_timer = 0.0     # 사자 포효 등으로 패닉 지속(초)

    def update(self, world, dt):
        if not self.alive:
            return
        self.age += dt
        self.hunger = min(100.0, self.hunger + 2.4 * dt)
        self.thirst = min(100.0, self.thirst + 2.1 * dt)
        self.recover_stamina(dt)

        # 패닉 상태: 감지 범위 2배, 스태미나 회복 절반(계획서)
        if self.panic_boost_timer > 0:
            self.panic_boost_timer = max(0.0, self.panic_boost_timer - dt)
            self.panic_range = self.base_panic_range * 2.0
            self.stamina_recovery_rate = 3.5
        else:
            self.panic_range = self.base_panic_range
            self.stamina_recovery_rate = 7.0

        if not self.behave(world, dt):
            self.wander(dt)

    def behave(self, world, dt):
        threat = world.nearest_predator(self, self.panic_range)
        self.is_chased = threat is not None
        if threat is not None:
            self.fight_or_flight(threat, world, dt)
            return True
        if self.seek_water_if_needed(world):
            return True
        if self.seek_plants_if_needed(world):
            return True
        if self.hunger < 40.0:
            self.heal()
        return False

    def heal(self):
        """안전하고 배부를 때 체력 자연 회복."""
        self.health = min(self.max_health, self.health + 3.0)

    def fight_or_flight(self, threat, world, dt):
        """기본은 도주(Flight). 종별로 Fight 를 오버라이드."""
        self.move_away_from(threat.position, self.flee_speed)
        self.action_text = "flee"
