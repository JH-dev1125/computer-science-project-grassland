# =============================================================================
# meerkat.py — 미어캣 (계획서 Meerkat, Omnivore 상속)
# 고유 속성: is_sentinel(보초 중인가), sentinel_height(보초 시 높이)
# 고유 메서드: stand()(보초 서기), eat_grass()
# 위협 시 동굴(Cave)로 숨는다.
# =============================================================================
from grassland.config import MEERKAT_HOME_RADIUS
from grassland.entities.animals.omnivores.omnivore import Omnivore


class Meerkat(Omnivore):
    def __init__(self, position):
        super().__init__("Meerkat", position, (198, 157, 93),
                         health=42.0, speed=82.0, power=5.0,
                         detect_range=130.0, radius=13.0)
        self.thirst_limit = 80.0   # 미어캣은 이슬 등으로 버텨 물을 늦게 찾는다
        self.food_range = 70.0         # 기본 먹이 탐지(detect_range=130)
        self._base_food_range = 70.0   # stand 해제 시 복원용
        self.diet_preference = 0.25
        self.aggression = 0.08
        self.is_sentinel = False
        self.sentinel_height = 0.0
        self.apocalypse = False   # 미어캣 엔딩 발동 시 True — 모든 것을 잡아먹는다
        self._grow = 0.0          # 거대화 진행도(0→1, world 가 갱신)

    SENTINEL_RANGE = 1.6      # 보초 설 때 탐지 범위 배율(넓게 살핀다)
    SENTINEL_DRAIN = 6.0      # 보초 서 있는 동안 초당 기력 소모(페널티)

    def stand(self, dt):
        """보초 서기 — 탐지 범위와 먹이 탐지 범위가 넓어지지만(SENTINEL_RANGE)
        가만히 서서 살피느라 기력을 계속 소모한다(SENTINEL_DRAIN)."""
        self.is_sentinel = True
        self.sentinel_height = 1.0
        self.food_range = self._base_food_range * self.SENTINEL_RANGE  # ~112
        self.stop()
        self.action_text = "stand"
        self.lose_energy(self.SENTINEL_DRAIN * dt)

    def eat_grass(self, grass):
        self.eat(grass)

    def devour(self, world, dt):
        """미어캣 엔딩 — 가장 가까운 대상(동물·식물·나무)으로 가서 먹어 치운다."""
        target = world.nearest_devour_target(self)
        if target is None:
            self.wander(world, dt)
            return True
        self.interaction_target = target
        if self.distance_to(target) <= self.radius + target.radius + 10:
            if hasattr(target, "diet_type"):     # 동물 → 공격(쿨다운 있음)
                self.attack(target, world)
            else:                                 # 식물·나무 → 베어 먹음
                target.consume(60)
            self.action_text = "devour"
        else:
            self.move_toward(target.position, self.speed)
            self.action_text = "hunt"
        return True

    def behave(self, world, dt):
        if self.apocalypse:                       # 엔딩 발동 → 모든 것을 잠식
            return self.devour(world, dt)
        # 보초는 감지 범위가 넓다(SENTINEL_RANGE 배)
        threat = world.nearest_predator(
            self, self.detect_range * (self.SENTINEL_RANGE if self.is_sentinel else 1.0))
        if threat is not None:
            cave = world.nearest_terrain_type("Cave", self.position)
            if cave is not None:
                self.move_toward(cave.position, self.speed * 1.2)
                if cave.contains(self):
                    self.is_hidden = True
                    self.stop()
                    self.action_text = "hide"
                else:
                    self.action_text = "cave"
                self.lose_energy(5.0 * dt)
                return True
            self.flee_or_fight(threat, world, dt)
            return True

        # 굴에서 너무 멀어지면 복귀
        cave = world.nearest_terrain_type("Cave", self.position)
        if cave is not None and self.distance_to(cave) > MEERKAT_HOME_RADIUS:
            self.move_toward(cave.position, self.speed)
            self.action_text = "return"
            self.lose_energy(4.0 * dt)
            return True

        # 배고프거나 목마르면 먼저 먹이·물 활동(잡식: 풀 또는 사체를 골라 먹음)
        self.is_sentinel = False
        self.sentinel_height = 0.0
        self.food_range = self._base_food_range   # 보초 해제 → 탐지 거리 복원
        if super().behave(world, dt):
            return True

        # 안전하고 배부르고 기력이 있으면 보초 서기(탐지↑·기력↓). 기력 없으면 어슬렁.
        if self.hunger < 60.0 and self.thirst < 60.0 and self.stamina > 20.0:
            self.stand(dt)
            return True
        return False
