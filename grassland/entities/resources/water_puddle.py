# water_puddle.py — 물웅덩이 (계획서 Water_Puddle, Resource 상속)
# evaporation 대신 가뭄 이벤트가 소모. reduce_thirst(), fill_rain()
#
#  [실행 흐름에서의 위치]
#    동물이 seek_water_if_needed → drink 로 마시는 대상(덕 타이핑 Drinkable).
#    가뭄(DroughtEvent)이 consume 으로 말리고, 비가 fill_rain/regenerate 로 채운다.
#    물웅덩이는 통과 못 하는 '벽'이기도 하다(world.obstacles).
from grassland.entities.resources.resource import Resource


class WaterPuddle(Resource):
    def __init__(self, position, amount=100.0):
        super().__init__("Water_Puddle", position, amount,
                         color=(65, 145, 208), radius=28)

    def reduce_thirst(self, animal):
        """동물이 한 모금 마신다 — 물이 조금 줄고 갈증이 가신다(덕 타이핑 Drinkable)."""
        # [←호출] Animal.drink 에서 source.reduce_thirst(self).
        taken = self.consume(5)                     # 한 모금에 5만큼 소모(다 마르면 사라짐)
        animal.thirst = max(0.0, animal.thirst - taken * 3.2)   # 마신 양의 3.2배만큼 갈증 감소

    def enable_drinking(self, animal):
        """drink 의 다른 진입점(같은 동작) — reduce_thirst 로 위임."""
        self.reduce_thirst(animal)

    def fill_rain(self):
        """비가 올 때 35만큼 차오른다."""
        self.regenerate(35)
