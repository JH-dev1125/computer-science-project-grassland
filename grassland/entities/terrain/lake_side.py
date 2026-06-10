# lake_side.py — 호숫가 (계획서 Lake_Side, Terrain 상속) : 음수 가능 지형
# 물의 양(water)이 있어 마시면 조금 줄고, 비가 오면 늘어난다(거의 마르지 않는 큰 수원).
from grassland.entities.terrain.terrain import Terrain


class LakeSide(Terrain):
    def __init__(self, position, size=82.0):
        super().__init__("Lake_Side", position, size, color=(79, 156, 201))
        self.water = 500.0          # 큰 수원 — 웅덩이보다 훨씬 많다
        self.max_water = 800.0

    def give_effect(self, entity):
        if hasattr(entity, "thirst"):
            entity.thirst = max(0.0, entity.thirst - 10.0)

    def reduce_thirst(self, animal):
        # 한 모금에 조금씩 — 물도 조금 줄고 갈증도 가신다
        taken = min(self.water, 5.0)
        self.water -= taken
        animal.thirst = max(0.0, animal.thirst - 18.0)

    def enable_drinking(self, animal):
        self.reduce_thirst(animal)

    def fill_rain(self, amount=60.0):
        """비가 오면 물이 불어난다."""
        self.water = min(self.max_water, self.water + amount)
