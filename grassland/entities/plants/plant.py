# =============================================================================
# entities/plants/plant.py — 모든 식물의 부모 (계획서 Plant)
# 속성: health, (x,y)=position, photosynthesis, spread
# 메서드: reproduce(), die(), consume()(섭취), photosynthesize()
# =============================================================================
#
#  [실행 흐름에서의 위치]
#    Grass/Bush/AcaciaTree/BaobabTree 의 부모. 매 프레임 world.update() 3단계의
#    'for plant in self.plants: plant.update(self, dt)' 에서 update() 가 호출되어 광합성으로
#    체력을 회복한다. 동물이 먹으면 consume() 으로 체력이 줄고, 0이 되면 die().
# =============================================================================
from grassland.entities.entity import Entity   # 부모(공통 좌표·표시 데이터)


class Plant(Entity):
    def __init__(self, name, position, health, max_health, color,
                 photosynthesis=1.0, radius=20):
        # [흐름] Entity 기본 초기화: kind="plant", solid=False(통과 가능), layer=1(바닥층)
        super().__init__(name=name, position=position, radius=radius,
                         color=color, kind="plant", solid=False, layer=1)
        self.health = health                    # [변수] 현재 체력(먹히면 줄고 광합성으로 회복)
        self.max_health = max_health            # [변수] 최대 체력
        self.photosynthesis = photosynthesis    # [변수] 초당 체력 회복량(광합성 속도)
        self.spread = 0.0                       # [변수] 번식 누적값(일정량 쌓이면 자식 식물 생성)

    def update(self, world, dt):
        """매 프레임 광합성으로 체력 회복(Entity.update 오버라이드)."""
        # [←호출] world.update() 3단계.
        if self.alive:
            # 날씨가 광합성(체력 회복) 속도에 영향 — 비 오면 빨리 자라고 가뭄이면 시든다.
            self.photosynthesize(dt * world.environment.growth_multiplier())

    def photosynthesize(self, dt):
        """체력을 photosynthesis × dt 만큼 회복(최대치 초과 금지)."""
        self.health = min(self.max_health, self.health + self.photosynthesis * dt)

    def reproduce(self):
        """번식 누적값 1 증가 → 외부에서 이 값을 확인해 자식 식물을 스폰."""
        self.spread += 1.0

    def consume(self, amount):
        """동물이 amount 만큼 먹으려 할 때, 실제 먹힌 양을 반환(덕 타이핑 Consumable)."""
        # [←호출] Animal.eat 안에서 food.consume(10) 형태로.
        eaten = min(self.health, amount)  # 남은 체력보다 많이 먹을 수 없음
        self.health -= eaten
        if self.health <= 0:
            self.die()                     # 다 먹히면 죽음
        return eaten                       # 실제 먹힌 양(동물의 허기를 이만큼 줄임)

    def die(self):
        """체력 소진 시: 렌더링·충돌 모두 비활성화."""
        self.alive = False
        self.solid = False
        self.action_text = "dead"
