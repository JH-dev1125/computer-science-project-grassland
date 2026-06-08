# lake_side.py — 호숫가 (계획서 Lake_Side, Terrain 상속) : 음수 가능 지형
from grassland.entities.terrain.terrain_base import Terrain


class LakeSide(Terrain):
    def __init__(self, position, size=82.0):
        super().__init__("Lake_Side", position, size, color=(79, 156, 201))

    def give_effect(self, entity):
        if hasattr(entity, "thirst"):
            entity.thirst = 0.0

    def reduce_thirst(self, animal):
        animal.thirst = 0.0

    def enable_drinking(self, animal):
        self.reduce_thirst(animal)
