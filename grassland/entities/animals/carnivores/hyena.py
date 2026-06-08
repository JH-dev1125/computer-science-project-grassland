# =============================================================================
# hyena.py — 하이에나 (계획서 Hyena, Carnivore 상속)
# 고유 속성: steal_prey_chance, stolen_prey  /  고유 메서드: steal_prey()
# 다른 포식자가 먹는 사체를 확률적으로 가로챈다.
# 가로채는 동안에는 평소보다 훨씬 빠르게 돌진해 '낚아채는' 듯한 모양새를 낸다.
# =============================================================================
from grassland.entities.animals.carnivores.carnivore import Carnivore
from grassland.entities.resources.carcass import Carcass


class Hyena(Carnivore):
    def __init__(self, position):
        super().__init__("Hyena", position, (156, 126, 82),
                         health=86.0, speed=76.0, power=15.0, detect_range=150.0)
        self.steal_prey_chance = 0.4    # 탈취 확률(health 높을수록 ↑)
        self.stolen_prey = None         # 가로챈 Carcass
        self.steal_dash_speed = self.speed * 2.2   # 가로채러 달려들 때의 돌진 속도(평소 이동의 2배 이상)
        self.steal_lunge_timer = 0.0    # 가로챈 직후 잠깐 그 속도를 유지 — '휙 낚아채는' 모션

    def steal_prey(self, carcass):
        """다른 포식자가 먹던 사체를 가로채 자신이 차지.
        가로채는 순간 사체 쪽으로 휙 튀어나가며, 잠깐 그 돌진 속도를 유지해
        실제로 '낚아채는' 듯한 모션을 만든다."""
        carcass.being_eaten_by = self
        self.stolen_prey = carcass
        self.action_text = "steal"
        self.steal_lunge_timer = 0.3
        self.move_toward(carcass.position, self.steal_dash_speed)

    def behave(self, world, dt):
        if self.steal_lunge_timer > 0.0:
            # 낚아채는 돌진 모션 중 — steering 이 dash 속도까지 끌어올릴 시간을 벌어 준다.
            self.steal_lunge_timer = max(0.0, self.steal_lunge_timer - dt)
            self.action_text = "steal"
            return True
        if self.hunger > 45.0:
            # 다른 포식자가 먹고 있는 사체를 노린다
            carcass = world.nearest_carcass(self.position)
            if isinstance(carcass, Carcass) and carcass.being_eaten_by is not None \
                    and carcass.being_eaten_by is not self:
                if self.distance_to(carcass) <= self.radius + carcass.radius + 12:
                    chance = self.steal_prey_chance * (self.health / self.max_health)
                    if __import__("random").random() < chance:
                        self.steal_prey(carcass)
                        return True
                else:
                    # 노리는 사체를 향해 평소 'carcass' 접근(speed*0.75)보다 훨씬 빠르게 돌진
                    self.move_toward(carcass.position, self.steal_dash_speed)
                    self.action_text = "steal_rush"
                    return True
        return super().behave(world, dt)
