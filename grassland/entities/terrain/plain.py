# plain.py — 평원 (계획서 Plain, Terrain 상속) : 배경 역할(효과 없음)
#
#  [실행 흐름] world.seed_structures() 가 맵 한가운데에 거대한 Plain 하나를 깐다.
#  give_effect 를 오버라이드하지 않아 아무 효과도 없다(physics 도 "Plain"은 건너뜀).
#  gui 는 이걸 개체로 그리지 않고 배경색/배경그림으로만 처리한다.
from grassland.entities.terrain.terrain import Terrain


class Plain(Terrain):
    def __init__(self, position, size=1000.0):
        # 풀밭색(126,184,92). size 가 커서 맵 전체를 덮는다.
        super().__init__("Plain", position, size, color=(126, 184, 92))
