# ────────────────────────────────────────────────────────────
#  [이후 코드 — 현재 파일]
# ────────────────────────────────────────────────────────────
# 데이터 흐름:
#   Animal.eat(acacia)
#     → acacia.consume(14)       : health 감소 + leaf_amount -= eaten*0.6
#     → acacia.on_eaten_by(animal): leaf>5이면 animal.health -= 4.0
# ────────────────────────────────────────────────────────────

from __future__ import annotations

from typing import TYPE_CHECKING

from grassland.entities.plants.plant import Plant
from pygame.math import Vector2

if TYPE_CHECKING:
    from grassland.world import World
    from grassland.entities.animals.animal import Animal


class AcaciaTree(Plant):
    def __init__(self, position: Vector2):
        super().__init__(
            name="Acacia_Tree",
            position=position,
            health=130.0,
            max_health=150.0,
            color=(97, 142, 63),
            photosynthesis=0.4,
        )
        self.thorn_damage = 4.0
        self.leaf_amount = 90.0
        self.max_leaf = 100.0
        self.radius = 34
        self._leaf_timer = 0.0  # 추가: 잎 재생 타이머

    def update(self, world: "World", dt: float) -> None:
        super().update(world, dt)
        if not self.alive:
            return
        self._leaf_timer += dt
        if self._leaf_timer >= 8.0:  # 8초마다 잎 재생
            self.produce_leaves()
            self._leaf_timer = 0.0

    def consume(self, amount: float) -> float:
        """잎도 같이 소모된다."""
        eaten = super().consume(amount)
        self.leaf_amount = max(0.0, self.leaf_amount - eaten * 0.6)
        return eaten

    def on_eaten_by(self, animal: "Animal") -> None:
        """잎이 남아 있을 때만 가시 피해를 입힌다."""
        if self.leaf_amount > 5.0:
            animal.health = max(0.0, animal.health - self.thorn_damage)
            animal.action_text = "thorned"

    def produce_leaves(self) -> None:
        """잎을 재생산하고 체력을 소량 회복(자가 광합성)."""
        self.leaf_amount = min(self.max_leaf, self.leaf_amount + 8.0)
        self.health = min(self.max_health, self.health + 5.0)

    def eat_leaves(self, amount: float) -> float:
        """코끼리 등이 잎을 뜯어 먹는다 — 먹은 양 반환."""
        taken = min(self.leaf_amount, amount)
        self.leaf_amount -= taken
        return taken

    def has_foliage(self) -> bool:
        """잎이 충분한가(부족하면 동물이 그늘·먹이로 모이지 않는다)."""
        return self.leaf_amount > 20.0

    def provide_shade(self, animal) -> None:
        """그늘: 동물 스트레스를 낮춘다(가뭄 더위 회피용)."""
        if hasattr(animal, "stress"):
            animal.stress = max(0.0, animal.stress - 5.0)
