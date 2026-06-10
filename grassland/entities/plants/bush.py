# bush.py — 덤불 (계획서 Bush, Plant 상속)
# current_foliage, stealth_factor / hide_entity()(은신), consume()(오버라이딩)
from grassland.entities.plants.plant import Plant


class Bush(Plant):
    def __init__(self, position):
        # 체력 80, 광합성 0.8/s(느림), 반경 30(넓음)으로 Plant 초기화
        super().__init__("Bush", position, health=80.0, max_health=80.0,
                         color=(47, 119, 67), photosynthesis=0.8, radius=30)
        self.current_foliage = 80.0   # 현재 잎 양 (먹힐수록 감소)
        self.max_foliage = 80.0       # 최대 잎 양
        self.stealth_factor = 0.65    # 은신 효과 계수 (잎이 많을수록 은신력↑)

    def hide_entity(self, entity):
        # 덤불 안에 있는 동물을 은신 상태로 만들고 스트레스를 낮춤
        ratio = self.current_foliage / self.max_foliage  # 잎이 많을수록 은신 효과 강함
        entity.is_hidden = True
        if hasattr(entity, "stress"):
            # 스트레스 = max(0, 현재 스트레스 - 은신효과)
            entity.stress = max(0.0, entity.stress - self.stealth_factor * ratio * 10.0)

    def consume(self, amount):
        # Plant.consume()으로 체력 감소 + 잎 양도 함께 감소
        eaten = super().consume(amount)
        self.current_foliage = max(0.0, self.current_foliage - eaten)
        return eaten
