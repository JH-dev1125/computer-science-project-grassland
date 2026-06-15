# =============================================================================
# warthog.py — 혹멧돼지 (계획서 Warthog, Omnivore 상속)
# 고유 속성: burrow_location(도주할 굴 위치)
# 고유 메서드: burrow()(굴로 도주), _engage()(접근·반격)
# =============================================================================
#
#  [실행 흐름에서의 위치]
#    Omnivore 상속. behave() 를 오버라이드해 '위협 시 굴로 도주(또는 약한 적엔 반격),
#    평소엔 물·약한 사냥감·먹이'를 판단한다.
# =============================================================================
from grassland.entities.animals.omnivores.omnivore import Omnivore


class Warthog(Omnivore):
    MAX_HIDE_DURATION = 5.0   # [변수] 굴 안에 최대 머물 수 있는 시간(초)

    def __init__(self, position):
        super().__init__("Warthog", position, (121, 95, 70),
                         health=72.0, speed=68.0, power=12.0,
                         detect_range=115.0, radius=18.0)
        self.thirst_limit = 72.0
        self.food_range = 85.0
        self.diet_preference = 0.35   # [변수] 약간 초식 선호
        self.aggression = 0.35        # [변수] 어느 정도 공격적
        self.burrow_location = None   # [변수] 도주해 숨을 굴 위치(기억용)
        self._burrow_cooldown = 0.0   # [변수] 굴 재진입 쿨타임(은신 후 5초)
        self._hiding = False          # [변수] 현재 굴 안에 은신 중인가
        self._hide_elapsed = 0.0      # [변수] 이번 은신이 시작된 뒤 경과 시간

    def burrow(self, world):
        """가까운 동굴로 전력 질주해 숨는다. 쿨타임 5초, 최대 3초간 은신."""
        cave = world.nearest_terrain_type("Cave", self.position)
        if cave is not None:
            self.burrow_location = cave.position.copy()
            self.move_toward(cave.position, self.speed * 1.8)   # 전력 질주(1.8배)
            if cave.contains(self):
                self.stop()
                if self._burrow_cooldown <= 0.0:   # 쿨타임 없을 때만 새로 은신 시작
                    self.is_hidden = True
                    self._burrow_cooldown = 3.0
                    self._hiding = True
                    self._hide_elapsed = 0.0
        else:
            self.burrow_location = self.position.copy()
            self.stop()
        self.action_text = "burrow"

    def _engage(self, target, world, dt):
        """대상에게 다가가 닿으면 공격(반격·사냥 공통 도우미)."""
        self.interaction_target = target
        if self.distance_to(target) <= self.radius + target.radius + 8:
            self.attack(target, world)
            self.lose_energy(7.0 * dt)
        else:
            self.move_toward(target.position, self.speed)
            self.action_text = "hunt"

    def behave(self, world, dt):
        """혹멧돼지 판단(Omnivore.behave 오버라이드)."""
        self._burrow_cooldown = max(0.0, self._burrow_cooldown - dt)

        # ── 굴 은신 중: 최대 5초, 굴 밖으로 밀리면 즉시 해제 ─────────────
        if self._hiding:
            self._hide_elapsed += dt
            cave = world.nearest_terrain_type("Cave", self.position)
            if cave is None or not cave.contains(self) \
                    or self._hide_elapsed >= self.MAX_HIDE_DURATION:
                self._hiding = False             # 시간 초과/굴 이탈 → 은신 종료
                self._hide_elapsed = 0.0
            else:
                self.is_hidden = True
                self.stop()
                self.action_text = "burrow"
                return True

        # [변수] healthy : 체력 55%↑ + 기력 35↑ 이면 맞설 만한 상태.
        healthy = self.health > self.max_health * 0.55 and self.stamina > 35.0

        threat = world.nearest_predator(self, self.detect_range)
        if threat is not None:
            if healthy and threat.health < threat.max_health * 0.5:
                self._engage(threat, world, dt)  # 내가 건강하고 적이 약하면 반격
                return True
            cave = world.nearest_terrain_type("Cave", self.position)
            near_cave = cave is not None and self.distance_to(cave) < 160.0
            if near_cave and self.distance_to(threat) < 48.0 and self.stamina > 18.0:
                self.attack(threat, world)       # 굴 근처 + 적이 코앞이면 그 자리에서 반격
                self.lose_energy(7.0 * dt)
            else:
                self.burrow(world)   # 쿨타임 중에도 굴 쪽으로 이동은 계속
            return True

        if self.seek_water_if_needed(world):
            return True

        if healthy and self.hunger > 45.0:
            prey = world.nearest_weak_or_prey(self, self.detect_range)
            if prey is not None:
                self._engage(prey, world, dt)    # 건강하고 배고프면 약한 사냥감 추격
                return True

        return self.search_food(world, dt)       # [호출→] Omnivore.search_food(사체·풀)
