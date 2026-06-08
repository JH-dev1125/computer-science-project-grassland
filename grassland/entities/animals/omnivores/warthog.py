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
        self.diet_preference = 0.35
        self.aggression = 0.35
        self.tusk_power = 11.0   # 엄니 반격 하향(포식자 즉사 방지)
        self.burrow_location = None

    def dig(self, world):
        self.action_text = "dig"
        return world.nearest_plant(self.position)

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

    def behave(self, world, dt):
        threat = world.nearest_predator(self, self.detect_range)
        if threat is not None:
            cave = world.nearest_terrain_type("Cave", self.position)
            near_cave = cave is not None and self.distance_to(cave) < 160.0
            if near_cave and self.distance_to(threat) < 48.0 and self.stamina > 18.0:
                self.yacha(threat, world)           # 굴 근처 → 맞섬
                self.lose_energy(10.0 * dt)
            else:
                self.burrow(world)                  # 아니면 굴로 도주
                self.lose_energy(6.0 * dt)
            return True
        if self.seek_water_if_needed(world):
            return True
        if self.hunger > 52.0:
            food = self.dig(world)
            if food is not None:
                if self.distance_to(food) <= self.radius + food.radius + 8:
                    self.eat(food)
                    self.stop()
                else:
                    self.move_toward(food.position, self.speed * 0.75)
                return True
        return False
