# acacia_tree.py — 아카시아 (계획서 Acacia_Tree, Plant 상속)
# thorn_damage, leaf_amount, max_leaf / produce_leaves()
from grassland.entities.plants.plant import Plant


class AcaciaTree(Plant):
    def __init__(self, position):
        super().__init__("Acacia_Tree", position, health=130.0, max_health=130.0,
                         color=(97, 142, 63), photosynthesis=1.0, radius=34)
        self.thorn_damage = 4.0   # 섭취하는 동물에게 주는 가시 피해
        self.leaf_amount = 90.0
        self.max_leaf = 100.0

    def produce_leaves(self):
        self.leaf_amount = min(self.max_leaf, self.leaf_amount + 8)
        self.health = min(self.max_health, self.health + 5)
