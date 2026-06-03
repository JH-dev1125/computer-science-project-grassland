from __future__ import annotations

from grassland.entities.base import Entity
from grassland.entities.terrain.terrain_base import Terrain
from grassland.geometry import Vec2


class Cave(Terrain):
    def __init__(self, position: Vec2, size: float = 64.0):
        super().__init__(name="Cave", position=position, size=size, color=(82, 75, 67))

    def give_effect(self, entity: Entity) -> None:
        entity.is_hidden = True  # type: ignore[attr-defined]
        entity.action_text = "hidden"
