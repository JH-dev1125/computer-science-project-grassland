# carcass.py — 사체 (계획서 Carcass, Resource 상속)
# 양(amount)이 있어 먹을수록 줄고, 0 이 되면 일정 시간(부패) 후 사라진다.
# 아무도 안 먹어도 시간이 지나면 서서히 분해되어 사라진다.
# being_eaten_by: 현재 먹는 포식자(하이에나 탈취·사자 포효 상호작용에 사용)
from grassland.entities.resources.resource import Resource


class Carcass(Resource):
    def __init__(self, position, amount=85.0):
        super().__init__("Carcass", position, amount,
                         color=(118, 72, 44), radius=20)
        self.decomposition_timer = 30.0   # 안 먹혀도 이 시간 뒤부터 서서히 분해
        self.rot_timer = 8.0              # 양이 0 이 된 뒤 완전히 사라지기까지(부패)
        self.carried_by = None
        self.being_eaten_by = None

    def consume(self, amount):
        """먹힌 만큼 양만 줄인다(여기선 삭제 안 함 — 소멸은 update 의 부패 처리에 맡김)."""
        taken = min(self.amount, amount)
        self.amount -= taken
        return taken

    def update(self, world, dt):
        if not self.alive:
            return
        if self.amount <= 0:                       # 다 먹힌 사체 → 부패 후 소멸
            self.rot_timer -= dt
            self.action_text = "rot"
            if self.rot_timer <= 0:
                self.delete()
            return
        self.decomposition_timer -= dt             # 안 먹히면 서서히 분해
        if self.decomposition_timer <= 0:
            self.amount = max(0.0, self.amount - 6.0 * dt)

    def reduce_hunger(self, animal):
        taken = self.consume(8)                     # 한 입에 조금씩
        animal.hunger = max(0.0, animal.hunger - taken)
