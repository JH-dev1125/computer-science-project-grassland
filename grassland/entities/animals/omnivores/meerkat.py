# =============================================================================
# meerkat.py — 미어캣 (계획서 Meerkat, Omnivore 상속)
# 고유 속성: is_sentinel(보초 중인가), sentinel_height(보초 시 높이)
# 고유 메서드: stand()(보초 서기), eat_grass()
# 위협 시 동굴(Cave)로 숨는다.
# =============================================================================
from grassland.entities.animals.omnivores.omnivore import Omnivore


class Meerkat(Omnivore):
    def __init__(self, position):
        super().__init__("Meerkat", position, (198, 157, 93),
                         health=42.0, speed=82.0, power=5.0,
                         detect_range=130.0, radius=13.0)
        self.diet_preference = 0.25
        self.aggression = 0.08
        self.is_sentinel = False
        self.sentinel_height = 0.0

    def stand(self):
        self.is_sentinel = True
        self.sentinel_height = 1.0
        self.stop()
        self.action_text = "stand"

    def eat_grass(self, grass):
        self.eat(grass)

    def behave(self, world, dt):
        # 보초는 감지 범위가 넓다
        threat = world.nearest_predator(
            self, self.detect_range * (1.25 if self.is_sentinel else 1.0))
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

        # 안전하고 배부르면 보초 서기
        if self.hunger < 70.0 and self.thirst < 70.0:
            self.stand()
            return True

        self.is_sentinel = False
        self.sentinel_height = 0.0
        return super().behave(world, dt)
