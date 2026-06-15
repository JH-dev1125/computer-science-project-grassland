# lake_side.py — 호숫가 (계획서 Lake_Side, Terrain 상속) : 음수 가능 지형
# 물의 양(water)이 있어 마시면 조금 줄고, 비가 오면 늘어난다(거의 마르지 않는 큰 수원).
#
#  [실행 흐름에서의 위치]
#    동물이 nearest_water 로 찾는 물 후보. drink → reduce_thirst 로 갈증을 푼다.
#    물웅덩이보다 물이 훨씬 많아 잘 안 마른다. 동시에 통과 못 하는 '벽'이다(world.obstacles).
from grassland.entities.terrain.terrain import Terrain


class LakeSide(Terrain):
    def __init__(self, position, size=82.0):
        super().__init__("Lake_Side", position, size, color=(79, 156, 201))
        self.water = 500.0          # [변수] 큰 수원 — 웅덩이보다 훨씬 많다
        self.max_water = 800.0      # [변수] 최대 물의 양(비로 차오르는 상한)

    def give_effect(self, entity):
        """호숫가 원 안에 들어온 동물의 갈증을 조금 풀어 준다(닿기만 해도 시원)."""
        # [←호출] physics.apply_terrain_effects.
        if hasattr(entity, "thirst"):
            entity.thirst = max(0.0, entity.thirst - 10.0)

    def reduce_thirst(self, animal):
        """동물이 한 모금 마신다 — 물이 조금 줄고 갈증이 크게 가신다(덕 타이핑 Drinkable)."""
        # [←호출] Animal.drink.
        taken = min(self.water, 5.0)
        self.water -= taken
        animal.thirst = max(0.0, animal.thirst - 18.0)

    def enable_drinking(self, animal):
        """drink 의 다른 진입점 — reduce_thirst 로 위임."""
        self.reduce_thirst(animal)

    def fill_rain(self, amount=60.0):
        """비가 오면 물이 불어난다(최대치까지)."""
        self.water = min(self.max_water, self.water + amount)
