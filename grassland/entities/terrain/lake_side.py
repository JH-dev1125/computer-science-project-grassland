from __future__ import annotations

from typing import TYPE_CHECKING

from grassland.entities.base import Entity
from grassland.entities.terrain.terrain_base import Terrain
from grassland.geometry import Vec2

if TYPE_CHECKING:
    from grassland.entities.animals.animal import Animal


class LakeSide(Terrain):
    def __init__(self, position: Vec2, size: float = 82.0):
        super().__init__(name="Lake_Side", position=position, size=size, color=(79, 156, 201))

    def give_effect(self, entity: Entity) -> None:
        entity.thirst = max(0.0, entity.thirst - 18.0)  # type: ignore[attr-defined]

    def reduce_thirst(self, animal: "Animal") -> None:
        animal.thirst = max(0.0, animal.thirst - 18.0)
