# =============================================================================
# entities/terrain/terrain.py — 모든 지형의 부모 (계획서 Terrain)
# 속성: (x,y)=position, size  /  메서드: contains(), give_effect()
# 지형은 통과 가능(solid=False)하며 '원 안에 들어오면 효과'를 준다.
# =============================================================================
#
#  [실행 흐름에서의 위치]
#    Plain/Cave/LakeSide 의 부모. 매 프레임 physics.apply_terrain_effects() 가
#    동물이 어느 지형 원 안에 있는지(contains) 검사해 give_effect() 로 효과를 준다.
# =============================================================================
from grassland.entities.entity import Entity


class Terrain(Entity):
    def __init__(self, name, position, size, color):
        # [흐름] Entity 초기화: kind="terrain", solid=False(통과 가능), layer=0(가장 아래).
        #        radius 에 size 를 넘겨, 충돌 반경 = 지형의 영향 원 크기로 둔다.
        super().__init__(name=name, position=position, radius=size,
                         color=color, kind="terrain", solid=False, layer=0)
        self.size = size      # [변수] 지형 영향 원의 반지름

    def contains(self, entity):
        """entity 가 이 지형 원 안에 있는가."""
        return self.distance_to(entity) <= self.size

    def can_enter(self, entity):
        """이 지형에 들어올 수 있는 entity 인가(자식이 오버라이드)."""
        return True

    def give_effect(self, entity):
        """원 안 entity 에 줄 효과(자식이 오버라이드). 기본은 효과 없음."""
        return None
