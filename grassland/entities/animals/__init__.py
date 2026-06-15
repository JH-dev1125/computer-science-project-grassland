# animals 패키지 — 모든 동물 클래스를 '한곳에서' 꺼내 쓰게 모아 준다.
#
# [문법] 아래처럼 하위 파일의 클래스들을 여기로 import 해 두면,
#        다른 파일에서 'from grassland.entities.animals import Lion' 처럼 짧게 쓸 수 있다
#        (긴 경로 'grassland.entities.animals.carnivores.lion' 를 외울 필요 없음).
# [흐름] world.py 가 이 한 줄로 8종 동물 클래스를 모두 가져온다.
from grassland.entities.animals.animal import Animal
from grassland.entities.animals.carnivores import BaldEagle, Carnivore, Hyena, Lion
from grassland.entities.animals.herbivores import Elephant, Gazelle, Herbivore, Zebra
from grassland.entities.animals.omnivores import Meerkat, Omnivore, Warthog

# [문법] __all__ : 'from ... import *' 시 내보낼 이름 목록(공개 API 명시).
__all__ = ["Animal", "Carnivore", "Herbivore", "Omnivore",
           "BaldEagle", "Hyena", "Lion", "Zebra", "Gazelle", "Elephant",
           "Meerkat", "Warthog"]
