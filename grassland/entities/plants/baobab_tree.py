# baobab_tree.py — 바오밥나무 (계획서 Baobab_Tree, Plant 상속)
# stored_water / provide_shade()
from grassland.entities.plants.plant import Plant


class BaobabTree(Plant):
    def __init__(self, position):
        super().__init__("Baobab_Tree", position, health=180.0, max_health=180.0,
                         color=(151, 120, 72), photosynthesis=0.6, radius=42)
        self.stored_water = 80.0   # 가뭄 때 동물에게 줄 수분

    def provide_shade(self, animal):
        """그늘 제공: 동물 스트레스를 낮춘다."""
        if hasattr(animal, "stress"):
            animal.stress = max(0.0, animal.stress - 5.0)
