# =============================================================================
# meerkat.py — 미어캣 (계획서 Meerkat, Omnivore 상속)
# 고유 속성: is_sentinel(보초 중인가), sentinel_height(보초 시 높이)
# 고유 메서드: stand()(보초 서기), _use_cave()(동굴 행동 통합), boss()(엔딩 모드)
# 위협 시 동굴(Cave)로 숨는다.
# =============================================================================
from grassland.config import MEERKAT_HOME_RADIUS
from grassland.entities.animals.omnivores.omnivore import Omnivore


class Meerkat(Omnivore):
    SENTINEL_RANGE = 1.6   # 보초 설 때 탐지 범위 배율 (넓게 살핀다)
    SENTINEL_DRAIN = 6.0   # 보초 서 있는 동안 초당 기력 소모 (페널티)

    def __init__(self, position):
        # 체력 42, 속도 82(빠름), 공격력 5(약함), 감지 130, 반경 13(작음)
        super().__init__("Meerkat", position, (198, 157, 93),
                         health=42.0, speed=82.0, power=5.0,
                         detect_range=130.0, radius=13.0)
        self.thirst_limit = 80.0
        self.food_range = 70.0
        self._base_food_range = 70.0
        self.diet_preference = 0.25
        self.aggression = 0.08
        self.is_sentinel = False
        self.sentinel_height = 0.0
        self.apocalypse = False         # 미어캣 엔딩 발동 시 True
        self._grow = 0.0                # 거대화 진행도 (0→1, world가 갱신)
        self._roam_chance = 0.15
        self._hide_timer = 0.0          # 위협 소멸 후에도 굴 안에 머무는 시간

    def stand(self, dt):
        """보초 서기 — 탐지·먹이 범위 확장, 기력 소모."""
        self.is_sentinel = True
        self.sentinel_height = 1.0
        self.food_range = self._base_food_range * self.SENTINEL_RANGE
        self.stop()
        self.action_text = "stand"
        self.lose_energy(self.SENTINEL_DRAIN * dt)

    def eat_grass(self, grass):
        self.eat(grass)

    def boss(self, world, dt):
        """미어캣 엔딩 — 가장 가까운 대상(동물·식물·나무)으로 가서 먹어 치운다."""
        target = world.nearest_devour_target(self)
        if target is None:
            self.wander(world, dt)
            return True
        self.interaction_target = target
        if self.distance_to(target) <= self.radius + target.radius + 10:
            if hasattr(target, "diet_type"):
                self.attack(target, world)
            else:
                target.consume(60)
            self.action_text = "boss"
        else:
            self.move_toward(target.position, self.speed)
            self.action_text = "hunt"
        return True

    def _use_cave(self, cave, dt, threatened=False):
        """동굴 행동 통합 — 안에 있으면 은신(hide), 밖이면 동굴로 이동(cave)."""
        if cave.contains(self):
            self.is_hidden = True
            self.action_text = "hide"
            to_center = cave.position - self.position
            if to_center.length() > 1.0:
                self.desired_velocity = to_center.normalize() * (self.speed * 0.20)
            else:
                self.stop()
            self.lose_energy(2.0 * dt)
        else:
            self.is_hidden = False
            self.action_text = "cave"
            self.move_toward(cave.position, self.speed * (1.2 if threatened else 1.0))
            self.lose_energy((5.0 if threatened else 4.0) * dt)

    def behave(self, world, dt):
        if self.apocalypse:
            return self.boss(world, dt)

        self._hide_timer = max(0.0, self._hide_timer - dt)

        threat = world.nearest_predator(
            self, self.detect_range * (self.SENTINEL_RANGE if self.is_sentinel else 1.0))

        if threat is not None:
            self._hide_timer = 4.5
            cave = world.nearest_terrain_type("Cave", self.position)
            if cave is not None:
                self._use_cave(cave, dt, threatened=True)
                return True
            self.flee_or_fight(threat, world, dt)
            return True

        # 위협이 사라져도 hide_timer가 남아있으면 굴 안에 계속 머문다
        if self._hide_timer > 0.0:
            cave = world.nearest_terrain_type("Cave", self.position)
            if cave is not None and cave.contains(self):
                self._use_cave(cave, dt)
                return True

        # 굴에서 너무 멀어졌으면 복귀
        cave = world.nearest_terrain_type("Cave", self.position)
        if cave is not None and self.distance_to(cave) > MEERKAT_HOME_RADIUS:
            self._roam = None
            self._use_cave(cave, dt)
            return True

        self.is_sentinel = False
        self.sentinel_height = 0.0
        self.food_range = self._base_food_range
        if super().behave(world, dt):
            return True

        if self.hunger < 60.0 and self.thirst < 60.0 and self.stamina > 20.0:
            self.stand(dt)
            return True
        return False

    def wander(self, world, dt):
        """roam 목적지를 굴 반경 안으로 제한한다."""
        cave = world.nearest_terrain_type("Cave", self.position)

        if cave is not None and self._roam is not None:
            if cave.position.distance_to(self._roam) > MEERKAT_HOME_RADIUS * 0.75:
                self._roam = None

        super().wander(world, dt)

        if cave is not None and self._roam is not None:
            if cave.position.distance_to(self._roam) > MEERKAT_HOME_RADIUS * 0.75:
                self._roam = None
