# baobab_tree.py — 바오밥나무 (계획서 Baobab_Tree, Plant 상속)
# stored_water / provide_shade(), 잎(leaf) 시스템: 동물이 잎을 먹고, 자가 광합성으로 회복.
#
#  [실행 흐름에서의 위치]
#    가장 크고 튼튼한 나무. 아카시아처럼 '벽'이자 코끼리 잎 먹이·그늘 제공원이지만
#    가시 피해는 없다. update() 가 8초마다 잎을 재생한다.
from grassland.entities.plants.plant import Plant


class BaobabTree(Plant):
    def __init__(self, position):
        super().__init__("Baobab_Tree", position, health=180.0, max_health=180.0,
                         color=(151, 120, 72), photosynthesis=0.6, radius=42)
        self.stored_water = 80.0   # [변수] 가뭄 때 동물에게 줄 수분(연출/확장용)
        self.leaf_amount = 120.0   # [변수] 현재 잎 양
        self.max_leaf = 140.0      # [변수] 최대 잎 양
        self._leaf_timer = 0.0     # [변수] 잎 재생 타이머

    def update(self, world, dt):
        """광합성(부모) + 8초마다 잎 재생."""
        super().update(world, dt)
        if not self.alive:
            return
        self._leaf_timer += dt
        if self._leaf_timer >= 8.0:          # 8초마다 잎 재생(자가 광합성)
            self.leaf_amount = min(self.max_leaf, self.leaf_amount + 9.0)
            self._leaf_timer = 0.0

    def eat_leaves(self, amount):
        """코끼리 등이 잎을 뜯어 먹는다 — 먹은 양 반환."""
        taken = min(self.leaf_amount, amount)
        self.leaf_amount -= taken
        return taken

    def has_foliage(self):
        """잎이 충분한가(그늘·먹이 대상 판정)."""
        return self.leaf_amount > 25.0

    def provide_shade(self, animal):
        """그늘 제공: 동물 스트레스를 낮춘다."""
        if hasattr(animal, "stress"):
            animal.stress = max(0.0, animal.stress - 5.0)
