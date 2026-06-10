# =============================================================================
# warthog.py — 혹멧돼지 (계획서 Warthog, Omnivore 상속)
# 고유 속성: tusk_power(엄니 위력), burrow_location(도주할 굴 위치)
# 고유 메서드: dig()(땅 파 먹이 찾기), burrow()(굴로 도주), Yacha()(굴 근처면 맞섬)
# =============================================================================
from grassland.entities.animals.omnivores.omnivore import Omnivore


class Warthog(Omnivore):
    def __init__(self, position):
        super().__init__("Warthog", position, (121, 95, 70),
                         health=72.0, speed=68.0, power=12.0,
                         detect_range=115.0, radius=18.0)
        self.thirst_limit = 72.0
        self.food_range = 85.0         # 식물·사체 탐지(detect_range=115)
        self.diet_preference = 0.35
        self.aggression = 0.35
        self.tusk_power = 11.0   # 엄니 반격 하향(포식자 즉사 방지)
        self.burrow_location = None

    def dig(self, world):
        self.action_text = "dig"
        return world.nearest_plant(self.position, self.food_range)

    def burrow(self, world):
        """가까운 동굴로 도주해 숨는다. 없으면 그 자리에 굴을 판다."""
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

    def yacha(self, threat, world):
        """굴이 근처에 있으면 엄니로 포식자에 맞선다(계획서 Yacha)."""
        old_power, self.power = self.power, self.tusk_power
        self.attack(threat, world)
        self.power = old_power
        self.action_text = "yacha"

    def _engage(self, target, world, dt):
        """대상으로 접근해, 사정권에 들면 엄니로 공격(yacha)."""
        self.interaction_target = target
        if self.distance_to(target) <= self.radius + target.radius + 8:
            self.yacha(target, world)
            self.lose_energy(8.0 * dt)
        else:
            self.move_toward(target.position, self.speed)
            self.action_text = "hunt"

    def behave(self, world, dt):
        # 상태 판단: 체력·기력이 넉넉하면 '싸울 수 있는 몸 상태'
        healthy = self.health > self.max_health * 0.55 and self.stamina > 35.0

        threat = world.nearest_predator(self, self.detect_range)
        if threat is not None:
            # 체력이 좋고 상대 포식자가 약하면(체력 50%↓) 한 번 맞서 싸워 고기를 노린다
            if healthy and threat.health < threat.max_health * 0.5:
                self._engage(threat, world, dt)
                return True
            # 아니면 굴 근처면 엄니로 맞서고, 아니면 굴로 도주
            cave = world.nearest_terrain_type("Cave", self.position)
            near_cave = cave is not None and self.distance_to(cave) < 160.0
            if near_cave and self.distance_to(threat) < 48.0 and self.stamina > 18.0:
                self.yacha(threat, world)
                self.lose_energy(10.0 * dt)
            else:
                self.burrow(world)
                self.lose_energy(6.0 * dt)
            return True

        if self.seek_water_if_needed(world):
            return True

        # 건강하면 사냥: 탐지범위 안 약한 동물(초식·잡식, 또는 약한 육식)을 공격해 고기 확보
        if healthy and self.hunger > 45.0:
            prey = world.nearest_weak_or_prey(self, self.detect_range)
            if prey is not None:
                self._engage(prey, world, dt)
                return True

        # 배고프면 식물·사체 (체력이 낮을 땐 사냥을 못 해 자연히 이쪽 = 안전한 채식)
        if self.hunger > 40.0:
            food = self.decide_food(world)
            if food is not None:
                if self.distance_to(food) <= self.radius + food.radius + 8:
                    self.eat(food)
                    self.stop()
                else:
                    self.move_toward(food.position, self.speed * 0.75)
                    # 풀을 향해 이동할 때는 dig() 를 호출해 "뿌리를 캐러 간다"는 행동 표시
                    if hasattr(food, 'photosynthesis'):
                        self.dig(world)   # action_text = "dig" 로 설정됨
                    else:
                        self.action_text = "forage"
                return True
            if self.hunger >= self.HUNGER_SEARCH_LEVEL:
                return self.search_for_food(world, "search_food")
        return False
