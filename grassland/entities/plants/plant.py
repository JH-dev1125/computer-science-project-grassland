# =============================================================================
# entities/plants/plant.py — 모든 식물의 부모 (계획서 Plant)
# 속성: health, (x,y)=position, photosynthesis, spread
# 메서드: reproduce(), die(), consume()(섭취), photosynthesize()
# =============================================================================
from grassland.entities.entity import Entity


class Plant(Entity):
    def __init__(self, name, position, health, max_health, color,
                 photosynthesis=1.0, radius=20):
        super().__init__(name=name, position=position, radius=radius,
                         color=color, kind="plant", solid=False, layer=1)
        self.health = health
        self.max_health = max_health
        self.photosynthesis = photosynthesis   # 초당 체력 회복(광합성)
        self.spread = 0.0                       # 번식 누적값

    def update(self, world, dt):
        if self.alive:
            # 날씨가 광합성(체력 회복) 속도에 영향 — 비 오면 빨리 자라고 가뭄이면 시든다.
            self.photosynthesize(dt * world.environment.growth_multiplier())

    def photosynthesize(self, dt):
        self.health = min(self.max_health, self.health + self.photosynthesis * dt)

    def reproduce(self):
        self.spread += 1.0

    def consume(self, amount):
        """동물이 섭취. 먹힌 양 반환, 체력 0 이하면 die()."""
        eaten = min(self.health, amount)
        self.health -= eaten
        if self.health <= 0:
            self.die()
        return eaten

    def die(self):
        self.alive = False
        self.solid = False
        self.action_text = "dead"
