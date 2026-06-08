# =============================================================================
# lion.py — 사자 (계획서 Lion, Carnivore 상속)
# 고유 속성: mane_size, mane_exist  /  고유 메서드: roar()(주변 Zebra 위협), hide()
# =============================================================================
from grassland.entities.animals.carnivores.carnivore import Carnivore


class Lion(Carnivore):
    def __init__(self, position):
        super().__init__("Lion", position, (207, 157, 74),
                         health=120.0, speed=84.0, power=22.0, detect_range=170.0)
        self.hunt_stamina_cost = 17.0
        self.acceleration = 48.0
        self.mane_size = 1.0
        self.mane_exist = True
        self._avoid_timer = 0.0
        self._last_elephant_pos = None

    def behave(self, world, dt):
        import random as _r
        if not self.is_sleeping and self.stamina > 30.0 and _r.random() < 0.004:
            self.roar(world)
            return True

        # 코끼리 감지 시 avoid 타이머 설정 — 타이머 동안은 다른 행동 불가
        elephant = world.nearest_named("Elephant", self.position, 120.0)
        if elephant is not None and self.distance_to(elephant) < 120.0:
            self._avoid_timer = 3.5
            self._last_elephant_pos = elephant.position.copy()

        self._avoid_timer = max(0.0, self._avoid_timer - dt)
        if self._avoid_timer > 0.0:
            if self._last_elephant_pos is not None:
                self.move_away_from(self._last_elephant_pos, self.speed)
            self.action_text = "avoid"
            return True

        if self.seek_water_if_needed(world):
            return True
        if self.hunger > 38.0:
            prey = self.find_prey(world)
            if prey is not None:
                self.hunt(prey, world, dt)
                return True
            carcass = world.nearest_carcass(self.position)
            if carcass is not None:
                self.interaction_target = carcass
                if self.distance_to(carcass) <= self.radius + carcass.radius + 8:
                    self.eat(carcass)
                    self.stop()
                else:
                    self.move_toward(carcass.position, self.speed * 0.75)
                    self.action_text = "carcass"
                return True
        return False

    def roar(self, world):
        """포효: 일정 범위 내 Zebra 의 panic 을 유발(직접 안 보여도 경계↑)."""
        for animal in world.living_animals():
            if animal.name == "Zebra" and self.distance_to(animal) <= 320.0:
                if hasattr(animal, "panic_boost_timer"):
                    animal.panic_boost_timer = 4.0
        self.action_text = "roar"

    def hide(self):
        """오버라이딩: 사자는 더 강력하게 숨는다."""
        self.is_hidden = True
        self.stealth = 0.32
        self.action_text = "hide"
