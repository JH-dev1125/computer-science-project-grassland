# grass.py — 풀 (계획서 Grass, Plant 상속) : growth_rate, spread_seeds()
from grassland.entities.plants.plant import Plant


class Grass(Plant):
    def __init__(self, position):
        super().__init__("Grass", position, health=55.0, max_health=55.0,
                         color=(83, 174, 80), photosynthesis=1.4, radius=16)
        self.growth_rate = 2.2   # 비 올 때 초당 추가 회복

    def update(self, world, dt):
        super().update(world, dt)
        if self.alive and world.environment.weather == "rain":
            self.health = min(self.max_health, self.health + self.growth_rate * dt)

    def spread_seeds(self):
        self.reproduce()
