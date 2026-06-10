# =============================================================================
# entities/terrain/terrain.py — 모든 지형의 부모 (계획서 Terrain)
# 속성: (x,y)=position, size  /  메서드: contains(), give_effect()
# 지형은 통과 가능(solid=False)하며 '원 안에 들어오면 효과'를 준다.
# =============================================================================
from grassland.entities.entity import Entity


class Terrain(Entity):
    def __init__(self, name, position, size, color):
        super().__init__(name=name, position=position, radius=size,
                         color=color, kind="terrain", solid=False, layer=0)
        self.size = size

    def contains(self, entity):
        """entity 가 이 지형 원 안에 있는가."""
        return self.distance_to(entity) <= self.size

    def can_enter(self, entity):
        """이 지형에 들어올 수 있는 entity 인가(자식이 오버라이드)."""
        return True

    def give_effect(self, entity):
        """원 안 entity 에 줄 효과(자식이 오버라이드)."""
        return None
