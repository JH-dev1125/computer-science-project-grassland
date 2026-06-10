# water_puddle.py — 물웅덩이 (계획서 Water_Puddle, Resource 상속)
# evaporation 대신 가뭄 이벤트가 소모. reduce_thirst(), fill_rain()
from grassland.entities.resources.resource import Resource


class WaterPuddle(Resource):
    def __init__(self, position, amount=100.0):
        super().__init__("Water_Puddle", position, amount,
                         color=(65, 145, 208), radius=28)

    def reduce_thirst(self, animal):
        # 한 모금에 조금씩 — 물도 조금 줄고 갈증도 조금 가신다(다 마르면 사라짐)
        taken = self.consume(5)
        animal.thirst = max(0.0, animal.thirst - taken * 3.2)

    def enable_drinking(self, animal):
        self.reduce_thirst(animal)

    def fill_rain(self):
        self.regenerate(35)
