# =============================================================================
# physics.py — 물리/공간 처리 (역할: Entity끼리·Entity↔맵 의 '물리적' 상호작용)
# geometry 연산을 실제 Entity·맵에 적용한다.
#   _separate            : solid 끼리 원-원 충돌로 밀어냄
#   _integrate           : 속도→위치 이동, 마찰 감속, 맵 경계 반사
#   apply_terrain_effects: Entity 가 Terrain 원 안이면 효과 발동(Entity↔맵)
#   neighbors            : 범위 내 Entity 목록(근접 질의) 제공
# '무엇을 할지(AI)'는 다루지 않는다 — 그건 각 종 클래스 몫.
# =============================================================================
from grassland.geometry import Vec2


class PhysicsEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.friction = 0.88   # 매 프레임 속도에 곱하는 마찰(감속)

    def update(self, entities, dt):
        """살아있는 entity 들의 충돌 분리 후 위치를 한 프레임 전진."""
        movable = [e for e in entities if getattr(e, "alive", True)]
        self._separate(movable)
        for entity in movable:
            self._integrate(entity, dt)

    def _integrate(self, entity, dt):
        entity.position = entity.position + entity.velocity * dt
        entity.velocity = entity.velocity * self.friction
        clamped = entity.position.clamp(
            entity.radius, entity.radius,
            self.width - entity.radius, self.height - entity.radius,
        )
        if clamped.x != entity.position.x:
            entity.velocity = Vec2(-entity.velocity.x * 0.2, entity.velocity.y)
        if clamped.y != entity.position.y:
            entity.velocity = Vec2(entity.velocity.x, -entity.velocity.y * 0.2)
        entity.position = clamped

    def _separate(self, entities):
        """solid 두 원이 겹치면 절반씩 반대로 밀어냄. radius=충돌 크기라 종별 크기 차이 자동 반영."""
        for i in range(len(entities)):
            first = entities[i]
            if not getattr(first, "solid", True):
                continue
            for second in entities[i + 1:]:
                if not getattr(second, "solid", True):
                    continue
                delta = second.position - first.position
                distance = delta.length()
                min_distance = first.radius + second.radius + 2
                if distance <= 0 or distance >= min_distance:
                    continue
                push = delta.normalized() * ((min_distance - distance) * 0.5)
                first.position = first.position - push
                second.position = second.position + push

    def apply_terrain_effects(self, entities, terrains):
        """entity 가 Terrain 원 안이면 그 지형 효과를 발동(예: 호숫가=갈증↓, 동굴=은신)."""
        for entity in entities:
            if not getattr(entity, "alive", True):
                continue
            for terrain in terrains:
                if terrain.name == "Plain":
                    continue
                if terrain.contains(entity):
                    terrain.give_effect(entity)

    def neighbors(self, center, radius, entities):
        """center 로부터 radius 안 살아있는 entity 목록(근접 질의)."""
        return [e for e in entities
                if getattr(e, "alive", True) and center.distance_to(e.position) <= radius]
