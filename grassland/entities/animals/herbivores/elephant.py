# ────────────────────────────────────────────────────────────
#  [이후 코드 — 현재 파일]
# ────────────────────────────────────────────────────────────
# 핵심 변경:
#   fight  = stomp() — 돌진(move_toward)+공격으로 포식자 쫓아냄
#   flight = 없음 (코끼리는 도망치지 않음)
# ────────────────────────────────────────────────────────────

from __future__ import annotations

import random
from typing import Optional, TYPE_CHECKING

from grassland.entities.animals.animal import Animal
from grassland.entities.animals.herbivores.herbivore import Herbivore
from pygame.math import Vector2

if TYPE_CHECKING:
    from grassland.world import World


class Elephant(Herbivore):
    def __init__(self, position: Vector2):
        # power 를 낮춰 '쫓아내는' 방어동물로(예전 28 은 포식자를 즉사시켰다).
        super().__init__(
            "Elephant", position, (132, 132, 123), 165.0, 34.0, 11.0, 150.0
        )
        self.radius = 28.0

    @property
    def is_hidden(self):
        return False

    @is_hidden.setter
    def is_hidden(self, value):
        pass

    def behave(self, world: "World", dt: float) -> bool:
        threat = world.nearest_predator(self, self.panic_range)
        if threat is not None:
            self.fight_or_flight(threat, world, dt)
            return True
        return self.seek_water_if_needed(world) or self.seek_plants_if_needed(world)

    @property
    def health(self):
        return self._health

    @health.setter
    def health(self, value):
        if hasattr(self, '_health') and value < self._health:
            damage = self._health - value
            if getattr(self, 'stamina', 100.0) < 30.0:
                damage *= 0.5   # 기력 부족 시 데미지 50% 감소
            self._health = max(0.0, self._health - damage)
        else:
            self._health = value

    def fight_or_flight(
        self, threat: Animal, world: Optional["World"], dt: float
    ) -> None:
        del dt
        if world is None:
            return
        if self.stamina < 30.0:
            # 기력 부족 — stomp 불가, 맞아도 50% 감소
            self.stop()
            self.action_text = "tired"
            return
        if self.distance_to(threat) <= self.radius + threat.radius + 24:
            self.stomp(threat, world)
        else:
            self.stop()
            self.action_text = "guard"

    def stomp(self, target: Animal, world: "World") -> None:
        """가까운 포식자를 공격하고 넉백+공중 바운스로 쫓아낸다."""
        self.lose_energy(30.0)   # stomp 시 기력 30 소모
        # 10% 확률로 강타 — 40 데미지 직접 적용
        if random.random() < 0.10:
            if target.alive:
                target.health -= 40
                target.stress = min(100.0, target.stress + 20.0)
                if target.health <= 0:
                    target.die(world)
        else:
            self.attack(target, world)

        # 코끼리 자신도 살짝 뛴다
        self._bounce_timer = 0.3
        self._bounce_duration = 0.3
        self._bounce_height = 18.0

        if not target.alive:
            self.action_text = "stomp"
            return

        # 대상 넉백 + 공중 바운스
        away = target.position - self.position
        if away.length_squared() > 1e-6:
            push = away.normalize()
            target.position = target.position + push * 25.0
            target.velocity = push * target.speed * 1.4
        target._bounce_timer = 0.55
        target._bounce_duration = 0.55
        target._bounce_height = 48.0
        self.action_text = "stomp"
