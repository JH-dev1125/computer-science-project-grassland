# =============================================================================
# elephant.py — 코끼리 (계획서 Elephant, Herbivore 상속)
# 핵심:
#   fight  = stomp() — 돌진(move_toward)+공격으로 포식자 쫓아냄
#   flight = 없음 (코끼리는 도망치지 않음)
# =============================================================================
#
#  [실행 흐름에서의 위치]
#    Herbivore 상속이지만 거의 다 오버라이드한다.
#    behave() : 가까운 포식자만 stomp 로 쫓아내고, 평소엔 물·나무잎/풀을 먹으며 어슬렁댄다.
#    is_hidden·health 를 @property 로 덮어써 '숨을 수 없고, 기력 낮을 때 피해 절반'인 무적형 방어자.
# =============================================================================
from __future__ import annotations   # [문법] 타입 힌트 늦은 평가(전방 참조 허용)

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
        # 인자 순서: name, position, color, health, speed, power, detect_range
        super().__init__(
            "Elephant", position, (132, 132, 123), 165.0, 62.0, 11.0, 150.0
        )
        self.radius = 28.0             # [변수] 가장 큰 충돌 크기
        self.thirst_limit = 48.0   # [변수] 코끼리는 물을 많이·자주 마신다(낮은 한계)
        self.food_range = 120.0        # [변수] 나무·풀 탐지 거리
        self._roam_chance = 0.75   # [변수] 먼 곳 로밍을 자주 잡아 꾸준히 돌아다님(정체 방지)
        self._stomp_hold = 0.0     # [변수] stomp 이미지를 유지하는 남은 시간(한 프레임에 안 사라지게)

    @property
    def is_hidden(self):
        """코끼리는 절대 숨지 못한다 — 항상 False 를 반환(@property 로 읽기를 가로챔)."""
        return False

    @is_hidden.setter
    def is_hidden(self, value):
        """is_hidden 에 무엇을 대입하든 무시(pass) — 다른 코드가 숨기려 해도 안 숨겨짐."""
        # [문법] @property + setter 로 '읽으면 항상 False, 써도 무시'를 강제. (부모의 일반 속성을 덮어씀)
        pass

    # 멀리 있는 포식자엔 반응하지 않고 계속 어슬렁댄다(가까이 와야 맞섬) — 멀리서부터 멈춰
    # '벽'처럼 길을 막던 문제 해결. 포식자는 코끼리를 피하므로 평소엔 거의 늘 움직인다.
    GUARD_RANGE = 90.0   # [변수] 이 거리 안의 포식자에게만 반응(맞섬)

    def behave(self, world: "World", dt: float) -> bool:
        """코끼리 판단: 가까운 포식자 stomp → 물 → 먹이."""
        threat = world.nearest_predator(self, self.GUARD_RANGE)
        if threat is not None:
            self.fight_or_flight(threat, world, dt)   # [호출→] fight_or_flight(=stomp)
            return True
        if self.seek_water_if_needed(world):
            return True
        return self.search_food(world, dt)            # [호출→] search_food

    def search_food(self, world, dt):
        """나무 잎을 우선으로 먹고, 없으면 풀(부모 search_food)을 먹는다."""
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
                    # [문법] A if 조건 else B : 나무면 잎(eat_leaves), 아니면 일반 섭취(consume).
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
        # 나무 잎 우선 탐색(잎이 충분한 나무만)
        tree = world.nearest_tree(self.position, self.detect_range, need_foliage=True)
        if tree is not None:
            self._committed_food = tree
            self.interaction_target = tree
            if self.distance_to(tree) <= self.radius + tree.radius + 12:
                if self._feed_ready():
                    eaten = tree.eat_leaves(10.0)   # [호출→] AcaciaTree/BaobabTree.eat_leaves
                    self.hunger = max(0.0, self.hunger - eaten)
                self.stop()
                self.action_text = "eat"
            else:
                self.move_toward(tree.position, self.speed * 0.7)
                self.action_text = "search_food"
            return True
        return super().search_food(world, dt)         # 나무가 없으면 부모(풀 먹기)로

    @property
    def health(self):
        """체력 읽기 — 내부 _health 를 돌려준다."""
        return self._health

    @health.setter
    def health(self, value):
        """체력 쓰기를 가로채, '피해'일 때만 기력 부족 시 절반으로 줄여 적용한다."""
        # [문법] @property/@setter 로 health 대입을 가로챈다. 줄어드는(피해) 경우에만 감면 로직 적용.
        if hasattr(self, '_health') and value < self._health:
            damage = self._health - value          # 받을 피해량
            if getattr(self, 'stamina', 100.0) < 30.0:
                damage *= 0.5   # 기력 부족 시 데미지 50% 감소
            self._health = max(0.0, self._health - damage)
        else:
            self._health = value                   # 회복·초기화는 그대로 반영

    def fight_or_flight(
        self, threat: Animal, world: Optional["World"], dt: float
    ) -> None:
        """코끼리는 도망 없음 — 가까우면 stomp, 아니면 정지(벽이 되지 않게)."""
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
            self.stomp(threat, world, dt)          # [호출→] stomp
        else:
            self.stop()                            # 멀면 가만히(쫓아가지 않음)

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
            self.attack(target, world)             # 평소엔 일반 공격(power=11)

        # 코끼리 자신도 살짝 뛴다 (gui 가 _bounce_* 를 읽어 통통 튀게 그림)
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
            target.position = target.position + push * 25.0      # 위치를 멀리 밀고
            target.velocity = push * target.speed * 1.4          # 그 방향으로 속도도 줌
        target._bounce_timer = 0.55      # 대상이 더 크게 튀어 오르게(gui 표현)
        target._bounce_duration = 0.55
        target._bounce_height = 48.0
        self.action_text = "stomp"
