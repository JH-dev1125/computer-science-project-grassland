# grass.py — 풀 (계획서 Grass, Plant 상속) : growth_rate, spread_seeds()
from grassland.entities.plants.plant import Plant


class Grass(Plant):
    def __init__(self, position):
        # 체력 55, 광합성 1.4/s, 반경 16으로 Plant 초기화
        super().__init__("Grass", position, health=55.0, max_health=55.0,
                         color=(83, 174, 80), photosynthesis=1.4, radius=16)
        self.growth_rate = 2.2   # 비 올 때 추가 회복량(초당)

    def update(self, world, dt):
        # 기본 광합성 처리(부모)
        super().update(world, dt)
        # 비가 오는 날씨면 growth_rate만큼 추가 회복
        if self.alive and world.environment.weather == "rain":
            self.health = min(self.max_health, self.health + self.growth_rate * dt)

    def spread_seeds(self):
        # 번식 누적값 증가 → Plant.reproduce() 위임
        self.reproduce()
