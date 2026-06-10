# =============================================================================
# entities/plants/plant.py — 모든 식물의 부모 (계획서 Plant)
# 속성: health, (x,y)=position, photosynthesis, spread
# 메서드: reproduce(), die(), consume()(섭취), photosynthesize()
# =============================================================================
from grassland.entities.base import Entity


class Plant(Entity):
    def __init__(self, name, position, health, max_health, color,
                 photosynthesis=1.0, radius=20):
        # Entity 기본 초기화: kind="plant", solid=False(통과 가능), layer=1(바닥층)
        super().__init__(name=name, position=position, radius=radius,
                         color=color, kind="plant", solid=False, layer=1)
        self.health = health                    # 현재 체력
        self.max_health = max_health            # 최대 체력
        self.photosynthesis = photosynthesis    # 초당 체력 회복량(광합성 속도)
        self.spread = 0.0                       # 번식 누적값 (일정량 쌓이면 자식 식물 생성)

    def update(self, world, dt):
        # 살아있을 때만 광합성으로 체력 회복
        if self.alive:
            self.photosynthesize(dt)

    def photosynthesize(self, dt):
        # 매 프레임 photosynthesis * dt 만큼 회복, max_health 초과 불가
        self.health = min(self.max_health, self.health + self.photosynthesis * dt)

    def reproduce(self):
        # 번식 누적값 1 증가 → 외부에서 이 값을 확인해 자식 식물을 스폰
        self.spread += 1.0

    def consume(self, amount):
        # 동물이 amount만큼 먹으려 할 때, 실제 먹힌 양을 반환
        eaten = min(self.health, amount)  # 남은 체력보다 많이 먹을 수 없음
        self.health -= eaten
        if self.health <= 0:
            self.die()
        return eaten

    def die(self):
        # 체력 소진 시 호출: 렌더링·충돌 모두 비활성화
        self.alive = False
        self.solid = False
        self.action_text = "dead"
