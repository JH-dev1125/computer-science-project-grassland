# cave.py — 동굴 (계획서 Cave, Terrain 상속) : 안에 들어오면 은신
from grassland.entities.terrain.terrain_base import Terrain


_CAVE_ALLOWED = {"Meerkat", "Warthog"}


class Cave(Terrain):
    def __init__(self, position, size=64.0):
        super().__init__("Cave", position, size, color=(82, 75, 67))

    def can_enter(self, entity):
        return entity.name in _CAVE_ALLOWED

    def give_effect(self, entity):
        entity.is_hidden = True
        entity.action_text = "hidden"
