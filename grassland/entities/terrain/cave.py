# cave.py — 동굴 (계획서 Cave, Terrain 상속) : 안에 들어오면 은신
#
#  [실행 흐름에서의 위치]
#    미어캣·혹멧돼지가 nearest_terrain_type("Cave", ...) 로 찾아 숨는 곳.
#    physics.apply_terrain_effects 가 동굴 원 안의 동물에게 give_effect 를 적용한다.
from grassland.entities.terrain.terrain import Terrain


# [변수] _CAVE_ALLOWED : 동굴 효과를 받는 종(연출/확장용 참고 집합). 현재 효과는 미어캣에만 적용.
_CAVE_ALLOWED = {"Meerkat", "Warthog"}


class Cave(Terrain):
    def __init__(self, position, size=97.0):
        super().__init__("Cave", position, size, color=(82, 75, 67))

    def can_enter(self, entity):
        """모든 동물이 동굴을 통과할 수 있다(튕김 없음)."""
        # [참고] world.obstacles() 가 Cave 를 '벽'에서 제외하는 것과 짝을 이룬다(이중 처리 방지).
        return True

    def give_effect(self, entity):
        """동굴 원 안의 미어캣을 은신 상태로 만든다."""
        # [←호출] physics.apply_terrain_effects 가 매 프레임.
        if getattr(entity, "name", "") == "Meerkat":
            entity.is_hidden = True
            # "hidden"은 ANIMATIONS 에 없어 애니메이션이 깨졌다. "hide"로 통일.
            entity.action_text = "hide"
