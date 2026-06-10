# =============================================================================
# warthog.py — 혹멧돼지 (계획서 Warthog, Omnivore 상속)
# 고유 속성: burrow_location(도주할 굴 위치)
# 고유 메서드: burrow()(굴로 도주), _engage()(접근·반격)
# =============================================================================
from grassland.entities.animals.omnivores.omnivore import Omnivore


class Warthog(Omnivore):
    def __init__(self, position):
        # 체력 72(튼튼), 속도 68, 공격력 12, 감지 115, 반경 18
        super().__init__("Warthog", position, (121, 95, 70),
                         health=72.0, speed=68.0, power=12.0,
                         detect_range=115.0, radius=18.0)
        self.thirst_limit = 72.0
        self.food_range = 85.0          # 식물·사체 탐지 거리 (detect_range=115보다 좁음)
        self.diet_preference = 0.35     # 초식 약간 선호
        self.aggression = 0.35          # 중간 정도의 맞섬 성향
        self.burrow_location = None     # 마지막으로 확인한 굴 위치

    def burrow(self, world):
        # 가까운 동굴로 도주; 동굴이 없으면 현재 위치를 굴로 삼아 멈춤
        if self.action_text != "burrow":   # 새 도주 시작 시 1회성 비용
            self.lose_energy(20.0)
        cave = world.nearest_terrain_type("Cave", self.position)
        if cave is not None:
            self.burrow_location = cave.position.copy()
            self.move_toward(cave.position, self.speed * 1.15)
            if cave.contains(self):
                self.stop()
        else:
            self.burrow_location = self.position.copy()
            self.stop()
        self.action_text = "burrow"

    def _engage(self, target, world, dt):
        """대상으로 접근해, 사정권에 들면 공격."""
        self.interaction_target = target
        if self.distance_to(target) <= self.radius + target.radius + 8:
            self.attack(target, world)
            self.lose_energy(7.0 * dt)
        else:
            self.move_toward(target.position, self.speed)
            self.action_text = "hunt"

    def behave(self, world, dt):
        # 체력·기력이 넉넉하면 '싸울 수 있는 몸 상태'로 판단
        healthy = self.health > self.max_health * 0.55 and self.stamina > 35.0

        threat = world.nearest_predator(self, self.detect_range)
        if threat is not None:
            # 체력이 좋고 상대 포식자가 약하면(체력 50%↓) 맞서 싸워 고기를 노린다
            if healthy and threat.health < threat.max_health * 0.5:
                self._engage(threat, world, dt)
                return True
            # 굴이 160 이내에 있으면 "근처"로 판정
            cave = world.nearest_terrain_type("Cave", self.position)
            near_cave = cave is not None and self.distance_to(cave) < 160.0
            if near_cave and self.distance_to(threat) < 48.0 and self.stamina > 18.0:
                # 굴 근처 + 포식자 근접 + 기력 충분 → 반격
                self.attack(threat, world)
                self.lose_energy(7.0 * dt)
            else:
                # 그 외 → 굴로 도주 (burrow() 내부에서 1회성 비용 처리)
                self.burrow(world)
            return True

        # 갈증 우선 처리
        if self.seek_water_if_needed(world):
            return True

        # 건강하면 사냥: 탐지 범위 안 약한 동물을 공격해 고기 확보
        if healthy and self.hunger > 45.0:
            prey = world.nearest_weak_or_prey(self, self.detect_range)
            if prey is not None:
                self._engage(prey, world, dt)
                return True

        # 배고프면 식물·사체 탐색 (체력 낮을 땐 사냥 못 해 자연히 채식)
        return self.search_food(world, dt)
