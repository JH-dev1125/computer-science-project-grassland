# bush.py — 덤불 (계획서 Bush, Plant 상속)
# current_foliage, stealth_factor / hide_entity()(은신), consume()(오버라이딩)
from grassland.entities.plants.plant import Plant


class Bush(Plant):
    def __init__(self, position):
        super().__init__("Bush", position, health=80.0, max_health=80.0,
                         color=(47, 119, 67), photosynthesis=0.8, radius=30)
        self.current_foliage = 80.0
        self.max_foliage = 80.0
        self.stealth_factor = 0.65   # 잎이 많을수록 은신 효과↑

    def hide_entity(self, entity):
        """덤불 안 동물의 스트레스를 잎 비율만큼 낮춰 은신시킨다."""
        ratio = self.current_foliage / self.max_foliage
        entity.is_hidden = True
        if hasattr(entity, "stress"):
            entity.stress = max(0.0, entity.stress - self.stealth_factor * ratio * 10.0)

    def consume(self, amount):
        """오버라이딩: 먹히면 current_foliage 도 함께 감소."""
        eaten = super().consume(amount)
        self.current_foliage = max(0.0, self.current_foliage - eaten)
        return eaten
