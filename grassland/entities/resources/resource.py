# =============================================================================
# entities/resources/resource.py — 모든 소모성 자원의 부모 (계획서 Resource)
# 속성: (x,y)=position, amount  /  메서드: consume(), regenerate(), delete()
# =============================================================================
from grassland.entities.base import Entity


class Resource(Entity):
    def __init__(self, name, position, amount, color, radius=18):
        super().__init__(name=name, position=position, radius=radius,
                         color=color, kind="resource", solid=False, layer=1)
        self.amount = amount
        self.max_amount = amount

    def consume(self, amount):
        """amount 만큼 소모. 실제 소모량 반환, 0 이하면 delete()."""
        taken = min(self.amount, amount)
        self.amount -= taken
        if self.amount <= 0:
            self.delete()
        return taken

    def regenerate(self, amount):
        self.amount = min(self.max_amount, self.amount + amount)
        self.alive = True

    def delete(self):
        self.alive = False
