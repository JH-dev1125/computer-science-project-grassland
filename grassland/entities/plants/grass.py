# grass.py — 풀 (계획서 Grass, Plant 상속) : growth_rate, spread_seeds()
#
#  [실행 흐름] 가장 흔한 먹이. world.seed_grass()/regrow_plants() 가 맵에 깔고,
#  매 프레임 update() 로 광합성한다. 초식·미어캣이 consume() 으로 뜯어 먹는다.
from grassland.entities.plants.plant import Plant


class Grass(Plant):
    def __init__(self, position):
        # 체력 55, 광합성 1.4/s, 반경 16으로 Plant 초기화
        super().__init__("Grass", position, health=55.0, max_health=55.0,
                         color=(83, 174, 80), photosynthesis=1.4, radius=16)
        self.growth_rate = 2.2   # [변수] 비 올 때 추가 회복량(초당)

    def update(self, world, dt):
        """기본 광합성 + 비 오면 추가 성장(Plant.update 오버라이드)."""
        super().update(world, dt)              # [호출→] Plant.update(날씨 반영 광합성)
        # 비가 오는 날씨면 growth_rate만큼 추가 회복
        if self.alive and world.environment.weather == "rain":
            self.health = min(self.max_health, self.health + self.growth_rate * dt)

    def spread_seeds(self):
        """씨앗 퍼뜨리기 — Plant.reproduce() 위임(번식 누적값 증가)."""
        self.reproduce()
