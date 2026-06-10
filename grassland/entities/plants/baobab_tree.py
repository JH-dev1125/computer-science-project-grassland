# baobab_tree.py — 바오밥나무 (계획서 Baobab_Tree, Plant 상속)
# stored_water / provide_shade(), 잎(leaf) 시스템: 동물이 잎을 먹고, 자가 광합성으로 회복.
from grassland.entities.plants.plant import Plant


class BaobabTree(Plant):
    def __init__(self, position):
        super().__init__("Baobab_Tree", position, health=180.0, max_health=180.0,
                         color=(151, 120, 72), photosynthesis=0.6, radius=42)
        self.stored_water = 80.0   # 가뭄 때 동물에게 줄 수분
        self.leaf_amount = 120.0
        self.max_leaf = 140.0
        self._leaf_timer = 0.0

    def update(self, world, dt):
        super().update(world, dt)
        if not self.alive:
            return
        self._leaf_timer += dt
        if self._leaf_timer >= 8.0:          # 8초마다 잎 재생(자가 광합성)
            self.leaf_amount = min(self.max_leaf, self.leaf_amount + 9.0)
            self._leaf_timer = 0.0

    def eat_leaves(self, amount):
        taken = min(self.leaf_amount, amount)
        self.leaf_amount -= taken
        return taken

    def has_foliage(self):
        return self.leaf_amount > 25.0

    def provide_shade(self, animal):
        """그늘 제공: 동물 스트레스를 낮춘다."""
        if hasattr(animal, "stress"):
            animal.stress = max(0.0, animal.stress - 5.0)
