# =============================================================================
# physics.py — 이동/충돌 (조향 steering 기반)
#
# [핵심 아이디어 — boids 식 조향]
#   AI 가 적어 둔 '가고 싶은 속도'(desired_velocity)에, 매 프레임 세 가지 조향력을
#   더해 '합성 목표 속도'를 만든다:
#     ① 분리(separation) : 너무 가까운 다른 동물에게서 멀어지는 힘 → 떼가 자연히 퍼짐
#     ② 회피(avoidance)  : 나무·물가 같은 구조물을 미리 비껴 가는 힘 → 벽에 처박지 않음
#     ③ 가장자리(edges)  : 맵 끝 근처에서 안쪽으로 트는 힘 → 벽에 끼이지 않고 되돌아옴
#   그 합성 목표로 현재 속도를 '부드럽게 보간(_steer)'하므로 방향이 완만히 휘고,
#   추격·도주 같은 강한 의도는 그대로 드러난다(조향력은 본래 속도를 넘기지 않게 제한).
#   남은 미세 겹침만 마지막에 위치로 살짝 분리(_separate)한다 — 속도를 죽이지 않아
#   벽에서 튕기거나 비벼지는 현상이 없다.
# =============================================================================
from __future__ import annotations

import math

from pygame.math import Vector2


class PhysicsEngine:
    SEP_RANGE = 2.1     # (두 반지름 합) × 이 배율 안의 이웃을 밀어낸다(클수록 더 흩어짐)
    AVOID_PAD = 28.0    # 구조물에서 이만큼 더 앞서 피하기 시작
    EDGE_PAD = 40.0     # 맵 가장자리에서 이만큼 안쪽부터 안으로 조향

    def __init__(self, width: float, height: float) -> None:
        self.width = width
        self.height = height
        self.top_margin = 14   # 지평선 아래로만 다니도록 위쪽 여유(월드 y 최소값)

    def update(self, animals, obstacles, dt: float) -> None:
        """살아있는 동물들을 조향으로 한 프레임 전진시키고, 남은 겹침을 분리한다."""
        for a in animals:
            self._integrate(a, animals, obstacles, dt)
        self._separate(animals, obstacles)

    # ── 한 마리: 합성 조향 목표 → 부드러운 가감속 → 위치 이동 → 맵 안으로 ──
    def _integrate(self, a, animals, obstacles, dt: float) -> None:
        self._steer(a, self._desired(a, animals, obstacles), dt)
        a.position += a.velocity * dt
        r = a.radius
        top = max(r, self.top_margin)
        # 맵 안으로 고정하고, '벽을 향해 파고드는' 속도 성분은 0 으로 — 벽을 응시하며
        # 멈춰 서거나 벽을 미는 일이 없게 한다(방향 표시는 velocity 를 따르므로 안쪽을 봄).
        if a.position.x < r:
            a.position.x, a.velocity.x = r, max(0.0, a.velocity.x)
        elif a.position.x > self.width - r:
            a.position.x, a.velocity.x = self.width - r, min(0.0, a.velocity.x)
        if a.position.y < top:
            a.position.y, a.velocity.y = top, max(0.0, a.velocity.y)
        elif a.position.y > self.height:
            a.position.y, a.velocity.y = self.height, min(0.0, a.velocity.y)

    def _steer(self, a, target: Vector2, dt: float) -> None:
        """현재 속도를 목표 속도로 지수 보간(프레임레이트 무관). agility 클수록 빠릿."""
        a.velocity = a.velocity.lerp(target, 1.0 - math.exp(-a.agility * dt))

    def _desired(self, a, animals, obstacles) -> Vector2:
        sp = max(a.speed, 1.0)
        target = Vector2(a.desired_velocity)
        target += self._sep(a, animals) * sp
        target += self._avoid(a, obstacles) * sp * 1.4
        target += self._edges(a) * sp * 1.6   # 가장자리에선 강하게 안쪽으로 틀어 벽을 응시·정체하지 않게
        # 기력이 낮을수록 최고 속도를 깎는다(탈진 0 → 0.5배, 만땅 100 → 1.0배) = 지쳐서 느려짐
        fatigue = 0.5 + 0.5 * (getattr(a, "stamina", 100.0) / 100.0)
        cap = max(sp, a.desired_velocity.length()) * fatigue
        if target.length() > cap:
            target.scale_to_length(cap)
        return target

    @staticmethod
    def _repel(here: Vector2, there: Vector2, reach: float) -> Vector2:
        """here 가 there 로부터 reach 안이면, 멀어지는 방향으로 '가까울수록 센' 단위힘."""
        d = here - there
        dist = d.length()
        if 1e-6 < dist < reach:
            return d / dist * (1.0 - dist / reach)
        return Vector2()

    def _sep(self, a, animals) -> Vector2:
        # 지금 쫓는/상호작용하는 대상에게선 분리하지 않는다 → 포식자가 먹이에 끝까지 붙는다.
        target = getattr(a, "interaction_target", None)
        force = Vector2()
        for o in animals:
            if o is not a and o is not target:
                force += self._repel(a.position, o.position,
                                     (a.radius + o.radius) * self.SEP_RANGE)
        return force

    def _avoid(self, a, obstacles) -> Vector2:
        force = Vector2()
        for pos, br in obstacles:
            force += self._repel(a.position, pos, a.radius + br + self.AVOID_PAD)
        return force

    def _edges(self, a) -> Vector2:
        force, r, m = Vector2(), a.radius, self.EDGE_PAD
        top = max(r, self.top_margin)
        if a.position.x < r + m:
            force.x += 1.0 - (a.position.x - r) / m
        elif a.position.x > self.width - r - m:
            force.x -= 1.0 - (self.width - r - a.position.x) / m
        if a.position.y < top + m:
            force.y += 1.0 - (a.position.y - top) / m
        elif a.position.y > self.height - m:
            force.y -= 1.0 - (self.height - a.position.y) / m
        return force

    # ── 잔여 겹침 해결: 위치만 부드럽게 분리(속도 보존) ─────────────────
    def _separate(self, animals, obstacles) -> None:
        for _ in range(2):
            for i, a in enumerate(animals):
                if not a.solid:
                    continue
                for b in animals[i + 1:]:
                    if not b.solid:
                        continue
                    d = b.position - a.position
                    dist = d.length()
                    overlap = a.radius + b.radius - dist
                    if dist > 1e-6 and overlap > 0:
                        shift = d / dist * (overlap * 0.5)
                        a.position -= shift
                        b.position += shift
                for pos, br in obstacles:    # 구조물은 통과 불가 — 밖으로 밀고 파고드는 속도만 제거
                    d = a.position - pos
                    dist = d.length()
                    md = a.radius + br
                    if dist <= 1e-6:
                        a.position = pos + Vector2(md, 0)
                    elif dist < md:
                        n = d / dist
                        a.position = pos + n * md
                        vin = a.velocity.dot(n)
                        if vin < 0:                 # 벽으로 파고드는 성분만 제거 → 접선 미끄러짐만 남김
                            a.velocity -= n * vin

    # ── 지형 효과(은신·갈증 해소 등) — 이동이 아니라 '원 안 효과' 적용 ──
    def apply_terrain_effects(self, entities, terrains) -> None:
        for entity in entities:
            if not entity.alive:
                continue
            for terrain in terrains:
                if terrain.name != "Plain" and terrain.contains(entity):
                    terrain.give_effect(entity)
