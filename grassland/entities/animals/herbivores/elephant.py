# ────────────────────────────────────────────────────────────
#  [이후 코드 — 현재 파일]
# ────────────────────────────────────────────────────────────
# 핵심 변경:
#   fight  = stomp() — 돌진(move_toward)+공격으로 포식자 쫓아냄
#   flight = 없음 (코끼리는 도망치지 않음)
# ────────────────────────────────────────────────────────────

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from grassland.entities.animals.animal import Animal
from grassland.entities.animals.herbivores.herbivore import Herbivore
from pygame.math import Vector2

if TYPE_CHECKING:
    from grassland.world import World


class Elephant(Herbivore):
    def __init__(self, position: Vector2):
        super().__init__(
            "Elephant", position, (132, 132, 123), 165.0, 52.0, 28.0, 220.0
        )
        self.radius = 28.0

    def fight_or_flight(
        self, threat: Animal, world: Optional["World"], dt: float
    ) -> None:
        del dt  # 코끼리는 항상 돌진 — dt 불필요
        if world is not None:
            self.stomp(threat, world)

    def stomp(self, target: Animal, world: "World") -> None:
        """포식자를 향해 돌진하며 공격해 쫓아낸다."""
        self.move_toward(target.position, self.speed * 1.2)
        self.attack(target, world)
        self.action_text = "stomp"
