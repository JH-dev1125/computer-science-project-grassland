# =============================================================================
# lion.py — 사자 (계획서 Lion, Carnivore 상속)
# 고유 속성: mane_size, mane_exist  /  고유 메서드: roar()(주변 Zebra 위협), hide()
# =============================================================================
#
#  [실행 흐름에서의 위치]
#    Carnivore 를 상속. update()(=Carnivore.update) 안에서 behave() 가 불리는데,
#    Lion 은 이 behave() 를 더 정교한 '우선순위 판단'으로 오버라이드한다:
#      ① 코끼리 회피(타이머 유지) → ② 극도 굶주림 사냥 → ③ 물 → ④ 포효 → ⑤ 일반 사냥 → ⑥ 매복
# =============================================================================
from grassland.entities.animals.carnivores.carnivore import Carnivore   # 부모(포식자 공통)


class Lion(Carnivore):
    def __init__(self, position):
        # [←호출] World.seed_animals 가 Lion(pos) 로 생성. 색=(207,157,74) 황갈색.
        super().__init__("Lion", position, (207, 157, 74),
                         health=120.0, speed=84.0, power=22.0, detect_range=170.0)
        self.thirst_limit = 70.0       # [변수] 갈증 70 넘으면 물 찾기
        self.food_range = 130.0        # [변수] 사체 탐지 거리 — 독점 방지(detect_range=170보다 짧게)
        self.hunt_stamina_cost = 5.0   # [변수] 추격 소모(사자는 효율적이라 낮음)
        self.acceleration = 48.0       # [변수] 추격 가속(빠름)
        self.mane_size = 1.0           # [변수] 갈기 크기(연출/확장용)
        self.mane_exist = True         # [변수] 갈기 유무
        self._avoid_timer = 0.0        # [변수] 코끼리 회피를 유지하는 남은 시간(한 번 보면 3.5초간 피함)
        self._last_elephant_pos = None # [변수] 마지막으로 본 코끼리 위치(시야에서 사라져도 그 반대로 도망)

    def behave(self, world, dt):
        """사자 판단(Carnivore.behave 오버라이드). True 면 wander 생략."""
        import random as _r   # [문법] 함수 안 import + as 별칭. 이 메서드에서만 _r 로 짧게 쓴다.
        # 1순위: 즉각적 위협 — 코끼리 회피 (범위 확대 + 타이머)
        elephant = world.nearest_named("Elephant", self.position, 90.0)
        if elephant is not None and self.distance_to(elephant) < 90.0:
            self._avoid_timer = 3.5                      # 코끼리를 봤으면 3.5초간 회피 유지
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
                self.hunt(prey, world, dt)               # [호출→] Carnivore.hunt
                return True
        # 3순위: 갈증 해소
        if self.seek_water_if_needed(world):
            return True
        # 4순위: 포효 (안전하고 체력 충분할 때 가끔 — 0.4% 확률)
        if self.hunger < self.HUNGER_SEARCH_LEVEL and self.stamina > 30.0 and _r.random() < 0.004:
            self.roar(world)                             # [호출→] roar
            return True
        # 5순위: 일반 배고픔 — 코끼리 없는 먹이만
        if self.hunger > 38.0:
            prey = self.find_prey(world)
            if prey is not None and not self._elephant_near(world, prey.position):
                self.hunt(prey, world, dt)
                return True
            carcass = self.nearest_available_carcass(world, self.food_range)   # 산 사냥감 없으면 사체
            if carcass is not None and not self._elephant_near(world, carcass.position):
                self.interaction_target = carcass
                if self.distance_to(carcass) <= self.radius + carcass.radius + 8:
                    self.eat(carcass)
                    self.stop()
                else:
                    self.move_toward(carcass.position, self.speed * 0.75)
                    self.action_text = "search_food"
                return True
        # ambush는 사냥을 결심한 후(hunger > 55)에만 — 허기 낮을 때 남발 방지
        if self.hunger > 55.0:
            return self.ambush(world, dt)                # [호출→] Carnivore.ambush
        return False

    def roar(self, world):
        """포효: 일정 범위 내 Zebra 의 panic 을 유발(직접 안 보여도 경계↑)."""
        self.lose_energy(35.0)                           # 포효는 기력을 크게 쓴다
        for animal in world.living_animals():
            if animal.name == "Zebra" and self.distance_to(animal) <= 320.0:
                if hasattr(animal, "panic_boost_timer"):
                    animal.panic_boost_timer = 4.0        # 320px 안 얼룩말들 경계 4초 강화
        self.action_text = "roar"

    def hide(self):
        """오버라이딩: 사자는 더 강력하게 숨는다(갈기 덕에 덤불과 잘 섞임).
        carnivore.ambush() → self.hide() 경로로 실제 호출된다."""
        self.is_hidden = True
        self.stealth = 0.42   # 기본(0.4) 보다 약간 강한 사자 매복 은신력
        self.action_text = "hide"
