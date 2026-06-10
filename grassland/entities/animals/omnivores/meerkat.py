# =============================================================================
# meerkat.py — 미어캣 (계획서 Meerkat, Omnivore 상속)
# 고유 속성: is_sentinel(보초 중인가), sentinel_height(보초 시 높이)
# 고유 메서드: stand()(보초 서기), eat_grass()
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
        self.thirst_limit = 80.0        # 이슬 등으로 버텨 물을 늦게 찾는다
        self.food_range = 70.0          # 기본 먹이 탐지 거리
        self._base_food_range = 70.0    # stand 해제 시 복원용
        self.diet_preference = 0.25     # 초식 선호 (주로 식물)
        self.aggression = 0.08          # 거의 싸우지 않음 (도망 위주)
        self.is_sentinel = False        # 현재 보초 중 여부
        self.sentinel_height = 0.0      # 보초 시 뒷발로 서는 높이 (렌더링용)
        self.apocalypse = False         # 미어캣 엔딩 발동 시 True — 모든 것을 잡아먹는다
        self._grow = 0.0                # 거대화 진행도 (0→1, world가 갱신)
        self._roam_chance = 0.15        # 기본(0.4)보다 낮게 — 굴 멀리 로밍하지 않도록
        # 위협이 마지막으로 사라진 후 일정 시간은 굴 밖으로 나오지 않는다
        # (식사 후 살짝 정도 밖으로 나갔다가 다시 돌아오는 카이팅을 방지)
        self._hide_timer = 0.0

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
        # 풀을 먹는 편의 메서드 → Omnivore.eat() 위임
        self.eat(grass)

    def devour(self, world, dt):
        """미어캣 엔딩 — 가장 가까운 대상(동물·식물·나무)으로 가서 먹어 치운다."""
        target = world.nearest_devour_target(self)
        if target is None:
            self.wander(world, dt)
            return True
        self.interaction_target = target
        if self.distance_to(target) <= self.radius + target.radius + 10:
            if hasattr(target, "diet_type"):   # 동물 → 공격 (쿨다운 있음)
                self.attack(target, world)
            else:                               # 식물·나무 → 베어 먹음
                target.consume(60)
            self.action_text = "devour"
        else:
            self.move_toward(target.position, self.speed)
            self.action_text = "hunt"
        return True

    def _stay_in_cave(self, cave, dt):
        """굴 안에서 중심으로 살짝 당기는 힘을 준다.
        physics가 분리돼 굴 밖으로 밀어내면 다시 들어오도록 부드럽게 유도한다.
        이로 인해 들어왔다 나갔다 반복하는 카이팅이 방지된다."""
        self.is_hidden = True
        to_center = cave.position - self.position
        if to_center.length() > 1.0:
            # 굴 중심 쪽으로 부드럽게 당김 — 너무 세면 굴 안에서 진동할 수 있음
            self.desired_velocity = to_center.normalize() * (self.speed * 0.20)
        else:
            self.stop()
        self.action_text = "hide"
        self.lose_energy(2.0 * dt)

    def behave(self, world, dt):
        if self.apocalypse:                    # 엔딩 발동 → 모든 것을 잠식
            return self.devour(world, dt)

        # hide_timer 감소 — 위협이 마지막으로 사라진 후 일정 시간 동안은 무조건 굴에 있는다
        self._hide_timer = max(0.0, self._hide_timer - dt)

        # 보초 중이면 탐지 범위가 SENTINEL_RANGE 배 확장
        threat = world.nearest_predator(
            self, self.detect_range * (self.SENTINEL_RANGE if self.is_sentinel else 1.0))

        if threat is not None:
            self._hide_timer = 4.5   # 위협이 보일 때마다 4.5초 타이머 리셋
            cave = world.nearest_terrain_type("Cave", self.position)
            if cave is not None:
                if cave.contains(self):
                    # 이미 동굴 안 → 안에 머무르기
                    self._stay_in_cave(cave, dt)
                else:
                    # 아직 이동 중 → 속도 120%로 질주
                    self.move_toward(cave.position, self.speed * 1.2)
                    self.action_text = "cave"
                    self.lose_energy(5.0 * dt)
                return True
            # 동굴이 없으면 Omnivore 기본 도망/맞섬 처리
            self.flee_or_fight(threat, world, dt)
            return True

        # 위협이 사라져도 hide_timer가 남아있으면 굴 안에 계속 머문다 (카이팅 방지 핵심)
        if self._hide_timer > 0.0:
            cave = world.nearest_terrain_type("Cave", self.position)
            if cave is not None and cave.contains(self):
                self._stay_in_cave(cave, dt)
                return True
            # 굴 밖이면 hide_timer를 진행시키며 일반 행동 (위협 재감지 대기)

        # 굴에서 너무 멀어졌으면 복귀 — 복귀 중 정해진 목적지도 취소
        cave = world.nearest_terrain_type("Cave", self.position)
        if cave is not None and self.distance_to(cave) > MEERKAT_HOME_RADIUS:
            self._roam = None   # 귀환 중 정해진 목적지 취소
            self.move_toward(cave.position, self.speed)
            self.action_text = "return"
            self.lose_energy(4.0 * dt)
            return True

        # 배고프거나 목마르면 먹이·물 활동 (잡식: 풀 또는 사체를 골라 먹음)
        self.is_sentinel = False
        self.sentinel_height = 0.0
        self.food_range = self._base_food_range  # 보초 해제 → 탐지 거리 복원
        if super().behave(world, dt):
            return True

        # 안전하고 배부르고 기력이 있으면 보초 서기 (탐지↑·기력↓), 기력 없으면 어슬렁
        if self.hunger < 60.0 and self.thirst < 60.0 and self.stamina > 20.0:
            self.stand(dt)
            return True
        return False

    def wander(self, world, dt):
        """roam 목적지를 굴 반경 안으로 제한한다.
        기본 wander()는 월드 전체에서 랜덤 목적지를 잡아 MEERKAT_HOME_RADIUS 밖을
        향하게 만든다. 목적지가 반경 밖이면 취소 → roam→return 무한 루프를 막는다."""
        cave = world.nearest_terrain_type("Cave", self.position)

        # 현재 _roam이 반경 밖이면 미리 취소
        if cave is not None and self._roam is not None:
            if cave.position.distance_to(self._roam) > MEERKAT_HOME_RADIUS * 0.75:
                self._roam = None

        super().wander(world, dt)

        # super()가 새 _roam을 잡았을 수도 있으므로 다시 확인
        if cave is not None and self._roam is not None:
            if cave.position.distance_to(self._roam) > MEERKAT_HOME_RADIUS * 0.75:
                self._roam = None
