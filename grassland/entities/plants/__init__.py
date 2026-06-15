# plants 패키지 — 식물(부모 Plant + 4종)을 한곳에 모아 내보낸다.
# (world.py 가 'from grassland.entities.plants import Grass, AcaciaTree' 로 가져간다)
from grassland.entities.plants.plant import Plant
from grassland.entities.plants.grass import Grass
from grassland.entities.plants.bush import Bush
from grassland.entities.plants.acacia_tree import AcaciaTree
from grassland.entities.plants.baobab_tree import BaobabTree

__all__ = ["Plant", "Grass", "Bush", "AcaciaTree", "BaobabTree"]
