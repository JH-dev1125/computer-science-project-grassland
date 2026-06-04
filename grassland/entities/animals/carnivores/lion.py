# =============================================================================
# lion.py — 사자 (계획서 Lion, Carnivore 상속)
# 고유 속성: mane_size, mane_exist  /  고유 메서드: roar()(주변 Zebra 위협), hide()
# =============================================================================
from grassland.entities.animals.carnivores.carnivore import Carnivore


class Lion(Carnivore):
    def __init__(self, position):
        super().__init__("Lion", position, (207, 157, 74),
                         health=120.0, speed=82.0, power=22.0, detect_range=245.0)
        self.hunt_stamina_cost = 12.0
        self.mane_size = 1.0      # 클수록 couple 확률↑ (계획서)
        self.mane_exist = True

    def behave(self, world, dt):
        # 가끔 포효 → 주변 Zebra 패닉 (계획서 Lion-Zebra 상호작용)
        if not self.is_sleeping and self.stamina > 30.0 and __import__("random").random() < 0.004:
            self.roar(world)
            return True
        return super().behave(world, dt)

    def roar(self, world):
        """포효: 일정 범위 내 Zebra 의 panic 을 유발(직접 안 보여도 경계↑)."""
        for animal in world.living_animals():
            if animal.name == "Zebra" and self.distance_to(animal) <= 320.0:
                if hasattr(animal, "panic_boost_timer"):
                    animal.panic_boost_timer = 4.0
        self.action_text = "roar"

    def hide(self):
        """오버라이딩: 사자는 더 강력하게 숨는다."""
        self.is_hidden = True
        self.stealth = 0.32
        self.action_text = "hide"
