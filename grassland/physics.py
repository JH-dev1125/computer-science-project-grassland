# =============================================================================
# physics.py — 물리/공간 처리 (역할: Entity끼리·Entity↔맵 의 '물리적' 상호작용)
# pygame.math.Vector2 연산을 실제 Entity·맵에 적용한다.
#   _separate            : solid 끼리 원-원 충돌로 밀어냄
#   _steer               : desired_velocity 쪽으로 현재 velocity 를 '부드럽게' 보간
#   _integrate           : steering → 위치 이동 → 맵 경계 반사
#   apply_terrain_effects: Entity 가 Terrain 원 안이면 효과 발동(Entity↔맵)
#   neighbors            : 범위 내 Entity 목록(근접 질의) 제공
# '무엇을 할지(AI)'는 다루지 않는다 — 그건 각 종 클래스 몫.
#
# [steering 의 핵심]
#   velocity 를 desired_velocity 로 '한 번에' 바꾸지 않고, 매 프레임 일정 비율만
#   따라가게 한다(지수 평활). 비율 t = 1 - e^(-agility·dt) 라서 프레임레이트가
#   달라도 같은 '반응 속도'를 유지한다. agility 가 클수록 빠릿하게 방향을 튼다.
# =============================================================================
from __future__ import annotations

import math


class PhysicsEngine:
    def __init__(self, width: float, height: float) -> None:
        self.width = width
        self.height = height

    def update(self, entities, dt: float) -> None:
        """살아있는 entity 들의 충돌 분리 후, steering 으로 한 프레임 전진."""
        movable = [e for e in entities if e.alive]
        self._separate(movable)
        for entity in movable:
            self._steer(entity, dt)
            self._integrate(entity, dt)

    def _steer(self, entity, dt: float) -> None:
        """현재 속도를 원하는 속도(desired_velocity) 쪽으로 부드럽게 끌어당긴다."""
        agility = getattr(entity, "agility", 6.0)
        t = 1.0 - math.exp(-agility * dt)         # 0~1, 프레임레이트 무관
        entity.velocity = entity.velocity.lerp(entity.desired_velocity, t)

    def _integrate(self, entity, dt: float) -> None:
        entity.position = entity.position + entity.velocity * dt
        r = entity.radius
        x, y = entity.position.x, entity.position.y
        # 맵 경계: 부딪치면 살짝 튕기고, 랜덤워크 heading 도 안쪽으로 반사한다.
        if x < r:
            x, entity.velocity.x = r, abs(entity.velocity.x) * 0.3
            self._reflect_heading(entity, axis="x")
        elif x > self.width - r:
            x, entity.velocity.x = self.width - r, -abs(entity.velocity.x) * 0.3
            self._reflect_heading(entity, axis="x")
        if y < r:
            y, entity.velocity.y = r, abs(entity.velocity.y) * 0.3
            self._reflect_heading(entity, axis="y")
        elif y > self.height - r:
            y, entity.velocity.y = self.height - r, -abs(entity.velocity.y) * 0.3
            self._reflect_heading(entity, axis="y")
        entity.position.update(x, y)

    @staticmethod
    def _reflect_heading(entity, axis: str) -> None:
        """벽에 붙어 맴도는 것을 막으려 진행 방향(heading)을 안쪽으로 반사."""
        if not hasattr(entity, "heading"):
            return
        if axis == "x":
            entity.heading = 180.0 - entity.heading      # 세로 벽 기준 반사
        else:
            entity.heading = -entity.heading             # 가로 벽 기준 반사

    def _separate(self, entities) -> None:
        """solid 두 원이 겹치면 절반씩 반대로 밀어냄. radius=충돌 크기라 종별 크기 차이 자동 반영."""
        for i in range(len(entities)):
            first = entities[i]
            if not first.solid:
                continue
            for second in entities[i + 1:]:
                if not second.solid:
                    continue
                delta = second.position - first.position
                distance = delta.length()
                min_distance = first.radius + second.radius + 2
                if distance <= 0 or distance >= min_distance:
                    continue
                push = delta.normalize() * ((min_distance - distance) * 0.5)
                first.position = first.position - push
                second.position = second.position + push

    def apply_terrain_effects(self, entities, terrains) -> None:
        """entity 가 Terrain 원 안이면 그 지형 효과를 발동(예: 호숫가=갈증↓, 동굴=은신)."""
        for entity in entities:
            if not entity.alive:
                continue
            for terrain in terrains:
                if terrain.name == "Plain":
                    continue
                if terrain.contains(entity):
                    terrain.give_effect(entity)

    def neighbors(self, center, radius: float, entities):
        """center 로부터 radius 안 살아있는 entity 목록(근접 질의)."""
        return [e for e in entities
                if e.alive and center.distance_to(e.position) <= radius]
