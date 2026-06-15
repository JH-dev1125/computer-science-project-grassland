# =============================================================================
# meerkat.py — 미어캣 (계획서 Meerkat, Omnivore 상속)
# 고유 속성: is_sentinel(보초 중인가), sentinel_height(보초 시 높이)
# 고유 메서드: stand()(보초 서기), _use_cave()(동굴 행동 통합), boss()(엔딩 모드)
# 위협 시 동굴(Cave)로 숨는다.
# =============================================================================
#
#  [실행 흐름에서의 위치]
#    Omnivore 상속. behave()·wander() 를 오버라이드해 '굴 반경 안에서만 생활하고,
#    위협 시 동굴로 숨고, 평소엔 보초를 선다'를 구현한다. world 가 미어캣 엔딩을 켜면
#    apocalypse=True 가 되어 behave() 가 boss()(모든 것을 잡아먹기)로 분기한다.
# =============================================================================
from grassland.config import MEERKAT_HOME_RADIUS   # 굴에서 벗어날 수 있는 최대 거리
from grassland.entities.animals.omnivores.omnivore import Omnivore


class Meerkat(Omnivore):
    SENTINEL_RANGE = 1.6   # [변수] 보초 설 때 탐지 범위 배율 (넓게 살핀다)
    SENTINEL_DRAIN = 6.0   # [변수] 보초 서 있는 동안 초당 기력 소모 (페널티)

    def __init__(self, position):
        # 체력 42, 속도 82(빠름), 공격력 5(약함), 감지 130, 반경 13(작음)
        super().__init__("Meerkat", position, (198, 157, 93),
                         health=42.0, speed=82.0, power=5.0,
                         detect_range=130.0, radius=13.0)
        self.thirst_limit = 80.0
        self.food_range = 70.0
        self._base_food_range = 70.0    # [변수] 기본 먹이 범위(보초 끝나면 여기로 복귀)
        self.diet_preference = 0.25     # [변수] 초식 선호(0.25 = 풀을 더 자주)
        self.aggression = 0.08          # [변수] 거의 안 싸움(매우 소심)
        self.is_sentinel = False        # [변수] 지금 보초를 서고 있는가
        self.sentinel_height = 0.0      # [변수] 보초 시 일어선 높이(gui 표현)
        self.apocalypse = False         # [변수] 미어캣 엔딩 발동 시 True(world 가 켬)
        self._grow = 0.0                # [변수] 거대화 진행도 (0→1, world가 갱신)
        self._roam_chance = 0.15        # [변수] 굴 근처에서만 가끔 로밍(작게)
        self._hide_timer = 0.0          # [변수] 위협 소멸 후에도 굴 안에 머무는 잔여 시간

    def stand(self, dt):
        """보초 서기 — 탐지·먹이 범위 확장, 기력 소모."""
        self.is_sentinel = True
        self.sentinel_height = 1.0
        self.food_range = self._base_food_range * self.SENTINEL_RANGE   # 범위 1.6배
        self.stop()
        self.action_text = "stand"
        self.lose_energy(self.SENTINEL_DRAIN * dt)   # 보초는 기력을 계속 소모

    def eat_grass(self, grass):
        """풀 먹기(계획서 호환용 별칭) — 그냥 eat 으로 위임."""
        self.eat(grass)

    def boss(self, world, dt):
        """미어캣 엔딩 — 가장 가까운 대상(동물·식물·나무)으로 가서 먹어 치운다."""
        # [←호출] behave 에서 apocalypse 가 True 일 때.
        target = world.nearest_devour_target(self)   # [호출→] World.nearest_devour_target
        if target is None:
            self.wander(world, dt)
            return True
        self.interaction_target = target
        if self.distance_to(target) <= self.radius + target.radius + 10:
            if hasattr(target, "diet_type"):     # 동물이면 공격해서 죽임
                self.attack(target, world)
            else:                                # 식물/나무면 통째로 소모
                target.consume(60)
            self.action_text = "boss"
        else:
            self.move_toward(target.position, self.speed)
            self.action_text = "hunt"
        return True

    def _use_cave(self, cave, dt, threatened=False):
        """동굴 행동 통합 — 안에 있으면 은신(hide), 밖이면 동굴로 이동(cave)."""
        if cave.contains(self):                  # 굴 안에 있으면
            self.is_hidden = True
            self.action_text = "hide"
            to_center = cave.position - self.position
            if to_center.length() > 1.0:
                self.desired_velocity = to_center.normalize() * (self.speed * 0.20)  # 중앙으로 살살
            else:
                self.stop()
            self.lose_energy(2.0 * dt)
        else:                                    # 굴 밖이면 굴로 이동
            self.is_hidden = False
            self.action_text = "cave"
            # [문법] 1.2 if threatened else 1.0 : 위협받는 중이면 더 빠르게 굴로.
            self.move_toward(cave.position, self.speed * (1.2 if threatened else 1.0))
            self.lose_energy((5.0 if threatened else 4.0) * dt)

    def behave(self, world, dt):
        """미어캣 판단(Omnivore.behave 오버라이드)."""
        if self.apocalypse:                      # 엔딩 모드면 잡아먹기로 분기
            return self.boss(world, dt)

        self._hide_timer = max(0.0, self._hide_timer - dt)

        # 보초 중이면 탐지 범위를 넓혀 위협을 찾는다.
        threat = world.nearest_predator(
            self, self.detect_range * (self.SENTINEL_RANGE if self.is_sentinel else 1.0))

        # 타임어택 조건: 매우 배고프거나 매우 목마를 때 → 포식자를 무릅쓰고 먹이·물 확보
        _desperate = self.hunger > 75.0 or self.thirst >= self.thirst_limit

        if threat is not None:
            # 절박한 상태 + 포식자가 멀면 → 무시하고 활동 계속
            if _desperate and self.distance_to(threat) > 55.0:
                pass  # fall through — 타임어택(아래 일반 행동으로 내려감)
            else:
                self._hide_timer = 4.5           # 위협 사라져도 4.5초는 굴에 머묾
                cave = world.nearest_terrain_type("Cave", self.position)
                if cave is not None:
                    self._use_cave(cave, dt, threatened=True)   # [호출→] 동굴로 숨기
                    return True
                self.flee_or_fight(threat, world, dt)   # 굴이 없으면 도주/맞섬
                return True

        # 위협이 사라져도 hide_timer가 남아있으면 굴 안에 계속 머문다
        if self._hide_timer > 0.0:
            cave = world.nearest_terrain_type("Cave", self.position)
            if cave is not None and cave.contains(self):
                self._use_cave(cave, dt)
                return True

        # 굴에서 너무 멀어졌으면 복귀 — 타임어택(절박) 상태이거나 먹이·물 활동 중이면 허용
        cave = world.nearest_terrain_type("Cave", self.position)
        if cave is not None and self.distance_to(cave) > MEERKAT_HOME_RADIUS:
            _away_ok = _desperate or self.action_text in (
                "water", "drink", "eat", "search_food", "forage", "graze")
            if not _away_ok:
                self._roam = None
                self._use_cave(cave, dt)         # 굴로 복귀
                return True

        # 평소 활동: 보초 상태 해제 후 부모(Omnivore)의 일반 먹이·물 판단을 시도
        self.is_sentinel = False
        self.sentinel_height = 0.0
        self.food_range = self._base_food_range
        if super().behave(world, dt):            # [호출→] Omnivore.behave(물·먹이)
            return True

        # 한가하면 보초 서기
        if self.hunger < 60.0 and self.thirst < 60.0 and self.stamina > 20.0:
            self.stand(dt)
            return True
        return False

    def wander(self, world, dt):
        """wander를 굴 반경(MEERKAT_HOME_RADIUS) 안으로 완전히 제한한다.
        roam 목적지를 굴 중심에서 반경 안으로만 생성하고,
        heading drift가 경계 근처에 닿으면 굴 방향으로 틀어 와리가리를 방지한다."""
        # [문법] 함수 안 import : 이 메서드 안에서만 _r(random)·Vector2 를 쓰려고 지역 import.
        import random as _r
        from pygame.math import Vector2

        cave = world.nearest_terrain_type("Cave", self.position)

        # 반경 밖 roam 목적지 미리 취소(굴에서 너무 먼 목적지는 버림)
        if cave is not None and self._roam is not None:
            if cave.position.distance_to(self._roam) > MEERKAT_HOME_RADIUS * 0.80:
                self._roam = None

        # wander 타이머
        self.wander_timer -= dt
        if self.wander_timer <= 0.0:
            self.is_resting = _r.random() < 0.12
            self.wander_timer = _r.uniform(0.8, 2.2)
            self._cruise = self.speed * _r.uniform(0.30, 0.42)
            if self._roam is None and _r.random() < self._roam_chance:
                if cave is not None:
                    # 굴 반경 안 무작위 목적지(굴 중심에서 각도·거리로 한 점 잡기)
                    angle = _r.uniform(0.0, 360.0)
                    dist = _r.uniform(20.0, MEERKAT_HOME_RADIUS * 0.70)
                    raw = cave.position + Vector2(dist, 0.0).rotate(angle)
                    self._roam = Vector2(    # 맵 밖으로 안 나가게 가두기
                        max(20.0, min(raw.x, world.width - 20.0)),
                        max(20.0, min(raw.y, world.height - 20.0)))
                else:
                    self._roam = Vector2(
                        _r.uniform(0, world.width), _r.uniform(0, world.height))

        if self.is_resting:
            self.stop()
            self.action_text = "wander"
            return

        if self._roam is not None:
            to = self._roam - self.position
            if to.length() < 60.0:
                self._roam = None
            else:
                self.heading = Vector2(1.0, 0.0).angle_to(to)
                self.desired_velocity = to.normalize() * (self.speed * 0.5)
                self.action_text = "wander"
                return

        # heading drift — 경계 85% 근처이면 굴 쪽으로 heading 조정(밖으로 못 벗어나게)
        if cave is not None and self.distance_to(cave) > MEERKAT_HOME_RADIUS * 0.85:
            to_cave = cave.position - self.position
            if to_cave.length_squared() > 1e-6:
                self.heading = Vector2(1.0, 0.0).angle_to(to_cave)

        self.heading += _r.uniform(-45.0, 45.0) * dt   # 방향을 조금씩 흔들기
        self.desired_velocity = Vector2(1.0, 0.0).rotate(self.heading) * self._cruise
        self.action_text = "wander"
