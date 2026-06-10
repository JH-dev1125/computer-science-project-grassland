# plain.py — 평원 (계획서 Plain, Terrain 상속) : 배경 역할(효과 없음)
from grassland.entities.terrain.terrain import Terrain


class Plain(Terrain):
    def __init__(self, position, size=1000.0):
        super().__init__("Plain", position, size, color=(126, 184, 92))
