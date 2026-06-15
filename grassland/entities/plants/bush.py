# bush.py — 덤불 (계획서 Bush, Plant 상속)
# current_foliage, stealth_factor / hide_entity()(은신), consume()(오버라이딩)
#
#  [실행 흐름에서의 위치]
#    '은신처' 역할의 식물. 포식자 ambush(매복)와 초식 도주가 nearest_bush 로 이걸 찾고,
#    hide_entity() 로 그 안에 든 동물을 숨긴다(is_hidden=True). 통과 가능(solid=False).
from grassland.entities.plants.plant import Plant


class Bush(Plant):
    def __init__(self, position):
        # 체력 80, 광합성 0.8/s(느림), 반경 30(넓음)으로 Plant 초기화
        super().__init__("Bush", position, health=80.0, max_health=80.0,
                         color=(47, 119, 67), photosynthesis=0.8, radius=30)
        self.current_foliage = 80.0   # [변수] 현재 잎 양 (먹힐수록 감소 → 은신 효과↓)
        self.max_foliage = 80.0       # [변수] 최대 잎 양
        self.stealth_factor = 0.65    # [변수] 은신 효과 계수 (잎이 많을수록 은신력↑)

    def hide_entity(self, entity):
        """덤불 안 동물을 은신시키고 스트레스를 낮춘다."""
        # [←호출] Herbivore.behave / Carnivore.ambush 가 덤불에 닿았을 때.
        ratio = self.current_foliage / self.max_foliage  # [변수] 잎 충만도 0~1(많을수록 효과 강함)
        entity.is_hidden = True
        if hasattr(entity, "stress"):
            # 스트레스 = max(0, 현재 스트레스 - 은신효과)
            entity.stress = max(0.0, entity.stress - self.stealth_factor * ratio * 10.0)

    def consume(self, amount):
        """먹히면 체력과 함께 잎 양도 줄어든다(Plant.consume 오버라이드)."""
        eaten = super().consume(amount)        # [호출→] Plant.consume(체력 감소)
        self.current_foliage = max(0.0, self.current_foliage - eaten)
        return eaten
