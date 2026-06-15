# carnivores 패키지 — 육식동물(부모 Carnivore + 3종)을 한곳에 모아 내보낸다.
# (animals/__init__.py 가 'from ...carnivores import Lion' 로 이걸 다시 가져간다)
from grassland.entities.animals.carnivores.carnivore import Carnivore
from grassland.entities.animals.carnivores.lion import Lion
from grassland.entities.animals.carnivores.hyena import Hyena
from grassland.entities.animals.carnivores.bald_eagle import BaldEagle

__all__ = ["Carnivore", "Lion", "Hyena", "BaldEagle"]
