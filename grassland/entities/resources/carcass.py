# carcass.py — 사체 (계획서 Carcass, Resource 상속)
# decomposition_timer / reduce_hunger()
# being_eaten_by: 현재 먹는 포식자(하이에나 탈취·사자 포효 상호작용에 사용)
from grassland.entities.resources.resource import Resource


class Carcass(Resource):
    def __init__(self, position, amount=85.0):
        super().__init__("Carcass", position, amount,
                         color=(118, 72, 44), radius=20)
        self.decomposition_timer = 30.0   # 분해 시작까지 남은 시간(초)
        self.carried_by = None
        self.being_eaten_by = None

    def update(self, world, dt):
        """시간이 지나면 서서히 분해되어 사라진다."""
        if not self.alive:
            return
        self.decomposition_timer -= dt
        if self.decomposition_timer <= 0:
            self.amount = max(0.0, self.amount - 6.0 * dt)
            if self.amount <= 0:
                self.delete()

    def reduce_hunger(self, animal):
        taken = self.consume(22)
        animal.hunger = max(0.0, animal.hunger - taken)
