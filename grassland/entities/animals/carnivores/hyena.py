# =============================================================================
# hyena.py — 하이에나 (계획서 Hyena, Carnivore 상속)
# 고유 속성: steal_prey_chance
# hunt() 오버라이드: prey 가 사체를 먹고 있으면 탈취, 아니면 일반 사냥.
# 탈취·일반 사냥 모두 speed + acceleration 으로 속도 증가.
# =============================================================================
import random

from grassland.entities.animals.carnivores.carnivore import Carnivore
from grassland.entities.resources.carcass import Carcass


class Hyena(Carnivore):
    def __init__(self, position):
        super().__init__("Hyena", position, (156, 126, 82),
                         health=86.0, speed=76.0, power=15.0, detect_range=150.0)
        self.acceleration = 91.0         # Carnivore 기본값(34) 오버라이드 — speed+acceleration ≈ 167px/s
        self.thirst_limit = 66.0
        self.food_range = 110.0        # 사체 탐지 — detect_range=150
        self.steal_prey_chance = 0.4     # 탈취 확률(health 높을수록 ↑)

    def hunt(self, prey, world, dt):
        """Carnivore.hunt() 확장 — prey 가 사체를 먹고 있으면 탈취, 아니면 일반 사냥.
        돌진 속도는 모두 speed + acceleration 으로 통일."""
        carcass = world.nearest_carcass(prey.position)
        if isinstance(carcass, Carcass) and carcass.being_eaten_by is prey:
            # 탈취 모드: 접근 중이든 낚아채는 순간이든 모두 steal
            if self.action_text != "steal":   # 새 탈취 시작 시 1회성 비용
                self.lose_energy(25.0)
            self.interaction_target = carcass
            if self.distance_to(carcass) <= self.radius + carcass.radius + 12:
                if random.random() < self.steal_prey_chance * (self.health / self.max_health):
                    carcass.being_eaten_by = self
            self.move_toward(carcass.position, self.speed + self.acceleration)
            self.action_text = "steal"
            return
        # 일반 사냥
        super().hunt(prey, world, dt)

    def behave(self, world, dt):
        if self.hunger > 45.0:
            # 다른 포식자가 먹고 있는 사체를 노린다 — 경쟁자를 hunt() 에 넘긴다
            carcass = world.nearest_carcass(self.position, self.food_range)
            if isinstance(carcass, Carcass) and carcass.being_eaten_by is not None \
                    and carcass.being_eaten_by is not self:
                self.hunt(carcass.being_eaten_by, world, dt)
                return True
        return super().behave(world, dt)
