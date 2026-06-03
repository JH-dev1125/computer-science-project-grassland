from __future__ import annotations

from grassland.entities.base import Entity
from grassland.entities.plants.plant import Plant
from grassland.geometry import Vec2


class Bush(Plant):
    """
    초식동물이 육식동물을 피해 숨을 수 있는 덤불.

    속성:
        current_foliage: 현재 잎 양. consume()으로 섭취될수록 감소.
        max_foliage    : 초기 잎 최대값 (stealth_factor 계산 기준).
        stealth_factor : 완전한 잎 상태에서의 스트레스 감소량. 잎이 줄수록 효과 감소.
    """

    def __init__(self, position: Vec2):
        super().__init__(
            name="Bush",
            position=position,
            health=80.0,
            max_health=100.0,
            color=(47, 119, 67),
            photosynthesis=0.3,
        )
        self.current_foliage = 80.0
        self.max_foliage = 80.0    # stealth_factor 비율 계산 기준값
        self.stealth_factor = 0.65  # 완전 잎 상태에서의 최대 스트레스 감소량
        self.radius = 30

    # ── 메서드 ────────────────────────────────────────────────────────────────

    def hide_entity(self, entity: Entity) -> None:
        """
        개체를 덤불 안에 숨김 (오버로딩: stealth_factor에 현재 잎 비율을 반영).
        잎이 많을수록 은신 효과가 높고, 잎이 줄면 효과도 감소.
        """
        foliage_ratio = self.current_foliage / self.max_foliage
        effective_stealth = self.stealth_factor * foliage_ratio
        entity.is_hidden = True  # type: ignore[attr-defined]
        entity.stress = max(0.0, entity.stress - effective_stealth)  # type: ignore[attr-defined]
        entity.action_text = "hiding"

    def consume(self, amount: float) -> float:
        """오버라이딩: 섭취 시 current_foliage도 함께 감소."""
        eaten = super().consume(amount)
        self.current_foliage = max(0.0, self.current_foliage - eaten)
        return eaten
