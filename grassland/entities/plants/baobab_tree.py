from __future__ import annotations

from grassland.entities.base import Entity
from grassland.entities.plants.plant import Plant
from grassland.geometry import Vec2


class BaobabTree(Plant):
    """
    거대한 바오밥 나무. 내부에 물을 저장하며 동물에게 그늘을 제공.

    속성:
        stored_water: 저장된 물의 양. 가뭄 이벤트 시 동물이 활용 가능.
    """

    def __init__(self, position: Vec2):
        super().__init__(
            name="Baobab_Tree",
            position=position,
            health=180.0,
            max_health=200.0,
            color=(151, 120, 72),
            photosynthesis=0.2,
        )
        self.stored_water = 80.0  # 가뭄 시 동물에게 제공 가능한 수분
        self.radius = 42

    def provide_shade(self, animal: Entity) -> None:
        """동물에게 그늘을 제공해 스트레스를 감소."""
        animal.stress = max(0.0, animal.stress - 2.0)  # type: ignore[attr-defined]
