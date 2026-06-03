from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from grassland.world import World
from grassland.entities.plants.plant import Plant
from grassland.geometry import Vec2


class Grass(Plant):
    """
    초원의 기본 식물. 비가 올 때 growth_rate만큼 빠르게 성장.

    속성:
        growth_rate: 비(rain) 날씨일 때 초당 추가 체력 회복량.
    """

    def __init__(self, position: Vec2):
        super().__init__(
            name="Grass",
            position=position,
            health=55.0,
            max_health=70.0,
            color=(83, 174, 80),
            photosynthesis=0.5,
        )
        self.growth_rate = 2.2  # 비 날씨 시 초당 추가 회복량
        self.radius = 16

    def update(self, world: "World", dt: float) -> None:
        if not self.alive:
            return
        super().update(world, dt)  # 기본 광합성
        if world.environment.weather == "rain":
            self.health = min(self.max_health, self.health + self.growth_rate * dt)

    def spread_seeds(self) -> None:
        """씨앗을 퍼뜨림. World가 self.spread를 읽어 주변에 새 Grass 생성."""
        self.reproduce()
