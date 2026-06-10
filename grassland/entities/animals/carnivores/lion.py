# =============================================================================
# lion.py — 사자 (계획서 Lion, Carnivore 상속)
# 고유 속성: mane_size, mane_exist  /  고유 메서드: roar()(주변 Zebra 위협), hide()
# =============================================================================
from grassland.entities.animals.carnivores.carnivore import Carnivore


class Lion(Carnivore):
    def __init__(self, position):
        super().__init__("Lion", position, (207, 157, 74),
                         health=120.0, speed=84.0, power=22.0, detect_range=170.0)
        self.thirst_limit = 70.0
        self.food_range = 130.0        # 사체 탐지 — 독점 방지(detect_range=170)
        self.hunt_stamina_cost = 17.0
        self.acceleration = 48.0
        self.mane_size = 1.0
        self.mane_exist = True
        self._avoid_timer = 0.0
        self._last_elephant_pos = None

    def behave(self, world, dt):
        import random as _r
        # 1순위: 즉각적 위협 — 코끼리 회피 (범위 확대 + 타이머)
        elephant = world.nearest_named("Elephant", self.position, 90.0)
        if elephant is not None and self.distance_to(elephant) < 90.0:
            self._avoid_timer = 3.5
            self._last_elephant_pos = elephant.position.copy()
        self._avoid_timer = max(0.0, self._avoid_timer - dt)
        if self._avoid_timer > 0.0:
            if self._last_elephant_pos is not None:
                self.move_away_from(self._last_elephant_pos, self.speed)
            self.action_text = "avoid"
            return True
        # 2순위: 극도 굶주림 — 목표 근처에 코끼리 없을 때만 접근
        if self.hunger > 72.0:
            prey = self.find_prey(world)
            if prey is not None and not self._elephant_near(world, prey.position):
                self.hunt(prey, world, dt)
                return True
        # 3순위: 갈증 해소
        if self.seek_water_if_needed(world):
            return True
        # 4순위: 포효 (안전하고 체력 충분할 때 가끔)
        if self.hunger < self.HUNGER_SEARCH_LEVEL and self.stamina > 30.0 and _r.random() < 0.004:
            self.roar(world)
            return True
        # 5순위: 일반 배고픔 — 코끼리 없는 먹이만
        if self.hunger > 38.0:
            prey = self.find_prey(world)
            if prey is not None and not self._elephant_near(world, prey.position):
                self.hunt(prey, world, dt)
                return True
            carcass = self.nearest_available_carcass(world, self.food_range)
            if carcass is not None and not self._elephant_near(world, carcass.position):
                self.interaction_target = carcass
                if self.distance_to(carcass) <= self.radius + carcass.radius + 8:
                    self.eat(carcass)
                    self.stop()
                else:
                    self.move_toward(carcass.position, self.speed * 0.75)
                    self.action_text = "search_food"
                return True
        return self.ambush(world, dt)   # 먹이가 안 보이면 덤불에 숨어 기습 시도

    def roar(self, world):
        """포효: 일정 범위 내 Zebra 의 panic 을 유발(직접 안 보여도 경계↑)."""
        for animal in world.living_animals():
            if animal.name == "Zebra" and self.distance_to(animal) <= 320.0:
                if hasattr(animal, "panic_boost_timer"):
                    animal.panic_boost_timer = 4.0
        self.action_text = "roar"

    def hide(self):
        """오버라이딩: 사자는 더 강력하게 숨는다(갈기 덕에 덤불과 잘 섞임).
        carnivore.ambush() → self.hide() 경로로 실제 호출된다."""
        self.is_hidden = True
        self.stealth = 0.42   # 기본(0.4) 보다 약간 강한 사자 매복 은신력
        self.action_text = "hide"
