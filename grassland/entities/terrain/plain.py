from __future__ import annotations

from grassland.entities.terrain.terrain_base import Terrain
from grassland.geometry import Vec2


class Plain(Terrain):
    def __init__(self, position: Vec2, size: float = 1000.0):
        super().__init__(name="Plain", position=position, size=size, color=(126, 184, 92))
