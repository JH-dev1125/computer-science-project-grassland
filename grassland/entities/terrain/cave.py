# cave.py — 동굴 (계획서 Cave, Terrain 상속) : 안에 들어오면 은신
from grassland.entities.terrain.terrain import Terrain


_CAVE_ALLOWED = {"Meerkat", "Warthog"}


class Cave(Terrain):
    def __init__(self, position, size=97.0):
        super().__init__("Cave", position, size, color=(82, 75, 67))

    def can_enter(self, entity):
        return True   # 모든 동물이 동굴을 통과할 수 있다(튕김 없음)

    def give_effect(self, entity):
        if getattr(entity, "name", "") == "Meerkat":
            entity.is_hidden = True
            # "hidden"은 ANIMATIONS 에 없어 애니메이션이 깨졌다. "hide"로 통일.
            entity.action_text = "hide"
