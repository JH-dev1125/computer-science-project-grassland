# resources 패키지 — 자원(부모 Resource + 물웅덩이·사체)을 한곳에 모아 내보낸다.
from grassland.entities.resources.resource import Resource
from grassland.entities.resources.water_puddle import WaterPuddle
from grassland.entities.resources.carcass import Carcass

__all__ = ["Resource", "WaterPuddle", "Carcass"]
