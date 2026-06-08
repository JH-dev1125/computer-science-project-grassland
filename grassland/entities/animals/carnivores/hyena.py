# =============================================================================
# hyena.py — 하이에나 (계획서 Hyena, Carnivore 상속)
# 고유 속성: steal_prey_chance, stolen_prey  /  고유 메서드: steal_prey()
# 다른 포식자가 먹는 사체를 확률적으로 가로챈다.
# =============================================================================
from grassland.entities.animals.carnivores.carnivore import Carnivore
from grassland.entities.resources.carcass import Carcass


class Hyena(Carnivore):
    def __init__(self, position):
        super().__init__("Hyena", position, (156, 126, 82),
                         health=86.0, speed=76.0, power=15.0, detect_range=150.0)
        self.steal_prey_chance = 0.4    # 탈취 확률(health 높을수록 ↑)
        self.stolen_prey = None         # 가로챈 Carcass

    def steal_prey(self, carcass):
        """다른 포식자가 먹던 사체를 가로채 자신이 차지."""
        carcass.being_eaten_by = self
        self.stolen_prey = carcass
        self.action_text = "steal"

    def behave(self, world, dt):
        if self.hunger > 45.0:
            # 다른 포식자가 먹고 있는 사체를 노린다
            carcass = world.nearest_carcass(self.position)
            if isinstance(carcass, Carcass) and carcass.being_eaten_by is not None \
                    and carcass.being_eaten_by is not self \
                    and self.distance_to(carcass) <= self.radius + carcass.radius + 12:
                chance = self.steal_prey_chance * (self.health / self.max_health)
                if __import__("random").random() < chance:
                    self.steal_prey(carcass)
                    return True
        return super().behave(world, dt)
