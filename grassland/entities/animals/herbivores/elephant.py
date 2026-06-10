# ────────────────────────────────────────────────────────────
#  [이후 코드 — 현재 파일]
# ────────────────────────────────────────────────────────────
# 핵심 변경:
#   fight  = stomp() — 돌진(move_toward)+공격으로 포식자 쫓아냄
#   flight = 없음 (코끼리는 도망치지 않음)
# ────────────────────────────────────────────────────────────

from __future__ import annotations

import random
from typing import Optional, TYPE_CHECKING

from grassland.entities.animals.animal import Animal
from grassland.entities.animals.herbivores.herbivore import Herbivore
from pygame.math import Vector2

if TYPE_CHECKING:
    from grassland.world import World


class Elephant(Herbivore):
    def __init__(self, position: Vector2):
        # power 를 낮춰 '쫓아내는' 방어동물로(예전 28 은 포식자를 즉사시켰다).
        # speed 를 올려(34→62) 큰 몸집이 한자리에 멈춰 '벽'이 되어 길을 막지 않게 한다.
        super().__init__(
            "Elephant", position, (132, 132, 123), 165.0, 62.0, 11.0, 150.0
        )
        self.radius = 28.0
        self.thirst_limit = 48.0   # 코끼리는 물을 많이·자주 마신다
        self.food_range = 120.0        # 나무·풀 탐지(detect_range=150)
        self._roam_chance = 0.75   # 자주 먼 곳을 목적지로 잡아 꾸준히 맵을 돌아다닌다(정체 방지)
        self._stomp_hold = 0.0     # stomp 이미지를 이 시간 동안 계속 표시(즉시 사라지지 않도록)

    @property
    def is_hidden(self):
        return False

    @is_hidden.setter
    def is_hidden(self, value):
        pass

    # 멀리 있는 포식자엔 반응하지 않고 계속 어슬렁댄다(가까이 와야 맞섬) — 멀리서부터 멈춰
    # '벽'처럼 길을 막던 문제 해결. 포식자는 코끼리를 피하므로 평소엔 거의 늘 움직인다.
    GUARD_RANGE = 90.0

    def behave(self, world: "World", dt: float) -> bool:
        threat = world.nearest_predator(self, self.GUARD_RANGE)
        if threat is not None:
            self.fight_or_flight(threat, world, dt)
            return True
        if self.seek_water_if_needed(world):
            return True
        return self.search_food(world, dt)

    def search_food(self, world, dt):
        threshold = 20.0 if self.stamina < 25.0 else 40.0
        if self.hunger < threshold:
            self._committed_food = None
            return False
        # committed target 유지 (나무 또는 식물)
        if self._food_valid(self._committed_food):
            food = self._committed_food
            self.interaction_target = food
            if self.distance_to(food) <= self.radius + food.radius + 12:
                if self._feed_ready():
                    eaten = (food.eat_leaves(10.0) if hasattr(food, 'eat_leaves')
                             else food.consume(10))
                    self.hunger = max(0.0, self.hunger - eaten)
                self.stop()
                self.action_text = "eat"
            else:
                self.move_toward(food.position, self.speed * 0.7)
                self.action_text = "search_food"
            return True
        self._committed_food = None
        # 나무 잎 우선 탐색
        tree = world.nearest_tree(self.position, self.detect_range, need_foliage=True)
        if tree is not None:
            self._committed_food = tree
            self.interaction_target = tree
            if self.distance_to(tree) <= self.radius + tree.radius + 12:
                if self._feed_ready():
                    eaten = tree.eat_leaves(10.0)
                    self.hunger = max(0.0, self.hunger - eaten)
                self.stop()
                self.action_text = "eat"
            else:
                self.move_toward(tree.position, self.speed * 0.7)
                self.action_text = "search_food"
            return True
        return super().search_food(world, dt)

    @property
    def health(self):
        return self._health

    @health.setter
    def health(self, value):
        if hasattr(self, '_health') and value < self._health:
            damage = self._health - value
            if getattr(self, 'stamina', 100.0) < 30.0:
                damage *= 0.5   # 기력 부족 시 데미지 50% 감소
            self._health = max(0.0, self._health - damage)
        else:
            self._health = value

    def fight_or_flight(
        self, threat: Animal, world: Optional["World"], dt: float
    ) -> None:
        if world is None:
            return
        self._stomp_hold = max(0.0, self._stomp_hold - dt)
        # 홀드 중이면 stomp 이미지 유지 (중복 에너지 소모 없음)
        if self._stomp_hold > 0.0:
            self.action_text = "stomp"
            if self.distance_to(threat) <= self.radius + threat.radius + 24:
                self.attack(threat, world)
            return
        if self.distance_to(threat) <= self.radius + threat.radius + 24:
            self.stomp(threat, world, dt)
        else:
            self.stop()

    def stomp(self, target: Animal, world: "World", dt: float = 0.016) -> None:
        """가까운 포식자를 공격하고 넉백+공중 바운스로 쫓아낸다."""
        if self.stamina < 30.0:
            self.stop()
            return
        self.lose_energy(35.0 * dt)
        # stomp 이미지를 0.5초간 유지(이미지가 한 프레임에 사라지지 않도록)
        self._stomp_hold = 0.5
        # 10% 확률로 강타 — 40 데미지 직접 적용
        if random.random() < 0.10:
            if target.alive:
                target.health -= 40
                target.stress = min(100.0, target.stress + 20.0)
                if target.health <= 0:
                    target.die(world)
        else:
            self.attack(target, world)

        # 코끼리 자신도 살짝 뛴다
        self._bounce_timer = 0.3
        self._bounce_duration = 0.3
        self._bounce_height = 18.0

        if not target.alive:
            self.action_text = "stomp"
            return

        # 대상 넉백 + 공중 바운스
        away = target.position - self.position
        if away.length_squared() > 1e-6:
            push = away.normalize()
            target.position = target.position + push * 25.0
            target.velocity = push * target.speed * 1.4
        target._bounce_timer = 0.55
        target._bounce_duration = 0.55
        target._bounce_height = 48.0
        self.action_text = "stomp"
