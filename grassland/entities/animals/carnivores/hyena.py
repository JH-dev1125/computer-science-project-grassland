# =============================================================================
# hyena.py — 하이에나 (계획서 Hyena, Carnivore 상속)
# 고유 속성: steal_prey_chance
# hunt() 오버라이드: prey 가 사체를 먹고 있으면 탈취, 아니면 일반 사냥.
# ambush/stalk/hide 없음 — 덤불 근처 시 GUI 에서 반투명 효과만.
# =============================================================================
import random

from grassland.entities.animals.carnivores.carnivore import Carnivore
from grassland.entities.resources.carcass import Carcass


class Hyena(Carnivore):
    def __init__(self, position):
        super().__init__("Hyena", position, (156, 126, 82),
                         health=86.0, speed=76.0, power=15.0, detect_range=150.0)
        self.acceleration = 91.0
        self.thirst_limit = 66.0
        self.food_range = 130.0        # 사체 탐지 범위 확대(왕성한 처리)
        self.steal_prey_chance = 0.4

    def ambush(self, world, dt):
        """하이에나는 덤불 매복 없음."""
        return False

    def hunt(self, prey, world, dt):
        carcass = world.nearest_carcass(prey.position)
        if isinstance(carcass, Carcass) and carcass.being_eaten_by is prey:
            if self.action_text != "steal":
                self.lose_energy(25.0)
            self.interaction_target = carcass
            if self.distance_to(carcass) <= self.radius + carcass.radius + 12:
                if random.random() < self.steal_prey_chance * (self.health / self.max_health):
                    carcass.being_eaten_by = self
                    self._committed_food = carcass   # 탈취 성공 → 다음 프레임에 바로 eat
            self.move_toward(carcass.position, self.speed + self.acceleration)
            self.action_text = "steal"
            return
        super().hunt(prey, world, dt)

    def behave(self, world, dt):
        # 사체 왕성 처리: 낮은 허기에서도 사체·탈취 우선
        if self.hunger > 30.0:
            carcass = world.nearest_carcass(self.position, self.food_range)
            if isinstance(carcass, Carcass):
                # 다른 포식자(하이에나 제외)가 먹는 사체 → 탈취
                # 하이에나끼리는 스틸 금지 — 서로 뺏고 뺏기는 무한 순환 방지
                eater = carcass.being_eaten_by
                if eater is not None and eater is not self \
                        and getattr(eater, 'name', '') != 'Hyena':
                    self.hunt(eater, world, dt)
                    return True
                # 내가 소유 중이거나 주인 없는 사체 → 바로 먹기
                if (carcass.being_eaten_by is self or carcass.being_eaten_by is None) \
                        and not self._elephant_near(world, carcass.position):
                    self._committed_food = carcass
                    self.interaction_target = carcass
                    if self.distance_to(carcass) <= self.radius + carcass.radius + 8:
                        self.eat(carcass)
                        self.stop()
                    else:
                        self.move_toward(carcass.position, self.speed + self.acceleration)
                        self.action_text = "hunt"
                    return True
        return super().behave(world, dt)
