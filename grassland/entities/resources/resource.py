# =============================================================================
# entities/resources/resource.py — 모든 소모성 자원의 부모 (계획서 Resource)
# 속성: (x,y)=position, amount  /  메서드: consume(), regenerate(), delete()
# =============================================================================
#
#  [실행 흐름에서의 위치]
#    Carcass(사체)·WaterPuddle(물웅덩이)의 부모. '양(amount)이 있어 소모되는 것'을 표현한다.
#    매 프레임 world.update() 5단계에서 resource.update() 가 불린다(부패 등은 자식이 구현).
# =============================================================================
from grassland.entities.entity import Entity


class Resource(Entity):
    def __init__(self, name, position, amount, color, radius=18):
        # [흐름] Entity 초기화: kind="resource", solid=False(통과 가능), layer=1(바닥층)
        super().__init__(name=name, position=position, radius=radius,
                         color=color, kind="resource", solid=False, layer=1)
        self.amount = amount          # [변수] 현재 남은 양(먹거나 마시면 줄어듦)
        self.max_amount = amount      # [변수] 최대 양(채워지는 상한, 표시 단계 계산에도 사용)

    def consume(self, amount):
        """amount 만큼 소모. 실제 소모량 반환, 0 이하면 delete()."""
        taken = min(self.amount, amount)   # 남은 것보다 많이는 못 먹음
        self.amount -= taken
        if self.amount <= 0:
            self.delete()                  # 다 떨어지면 사라짐
        return taken

    def regenerate(self, amount):
        """양을 amount 만큼 회복(최대치까지). 비가 채워 줄 때 사용."""
        self.amount = min(self.max_amount, self.amount + amount)
        self.alive = True                  # 말랐다가 다시 차면 부활

    def delete(self):
        """소멸 표시(렌더·질의에서 제외)."""
        self.alive = False
