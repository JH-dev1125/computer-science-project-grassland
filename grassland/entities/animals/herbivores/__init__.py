# herbivores 패키지 — 초식동물(부모 Herbivore + 3종)을 한곳에 모아 내보낸다.
from grassland.entities.animals.herbivores.herbivore import Herbivore
from grassland.entities.animals.herbivores.zebra import Zebra
from grassland.entities.animals.herbivores.gazelle import Gazelle
from grassland.entities.animals.herbivores.elephant import Elephant

__all__ = ["Herbivore", "Zebra", "Gazelle", "Elephant"]
