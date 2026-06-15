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
#
#  [실행 흐름에서의 위치]
#    매 프레임 world.update() 의 '4단계'에서 physics.update(살아있는동물, 벽목록, dt) 호출.
#    이 시점엔 이미 3단계에서 각 동물이 desired_velocity(가고 싶은 속도)를 정해 둔 상태다.
#    physics 는 그 의도에 조향력을 더해 '실제 위치'를 옮기는 역할만 한다(무엇을 할지는 안 정함).
#
#  [한 동물의 처리 순서]  _integrate →  _desired(조향 합성) → _steer(보간) → 위치 이동 → 맵 안 고정
#                         그 뒤 전체에 대해 _separate(겹침 풀기)
# =============================================================================
# [문법] from __future__ import annotations : 타입 힌트(width: float 등)를 '문자열처럼' 늦게 평가하게 해
#        아직 정의 안 된 타입을 미리 적어도 에러가 안 나게 한다(전방 참조 허용). 동작에는 영향 없음.
from __future__ import annotations

import math   # [문법] exp(지수함수) 등 수학 함수. 프레임레이트 무관 보간에 사용.

from pygame.math import Vector2   # 2차원 벡터(이동·힘 계산)


class PhysicsEngine:
    # [문법] 클래스 바로 아래 변수 = '클래스 변수'(모든 인스턴스 공유 상수). 조향 세기 조절 손잡이.
    SEP_RANGE = 2.1     # [변수] (두 반지름 합) × 이 배율 안의 이웃을 밀어낸다(클수록 더 흩어짐)
    AVOID_PAD = 28.0    # [변수] 구조물에서 이만큼 더 앞서 피하기 시작
    EDGE_PAD = 65.0     # [변수] 맵 가장자리에서 이만큼 안쪽부터 안으로 조향

    def __init__(self, width: float, height: float) -> None:
        # [←호출] World.__init__ 에서 PhysicsEngine(width, height) 로 생성.
        self.width = width            # [변수] 맵 가로(경계 처리에 사용)
        self.height = height          # [변수] 맵 세로
        self.top_margin = 14   # [변수] 지평선 아래로만 다니도록 위쪽 여유(월드 y 최소값)

    def update(self, animals, obstacles, dt: float) -> None:
        """살아있는 동물들을 조향으로 한 프레임 전진시키고, 남은 겹침을 분리한다."""
        # [←호출] world.update() 4단계.
        # [변수] animals : 살아있는 동물 목록,  obstacles : (위치, 막는반지름) 벽 목록.
        for a in animals:
            self._integrate(a, animals, obstacles, dt)   # 한 마리씩 조향·이동
        self._separate(animals, obstacles)               # 그 뒤 전체 겹침 풀기

    # ── 한 마리: 합성 조향 목표 → 부드러운 가감속 → 위치 이동 → 맵 안으로 ──
    def _integrate(self, a, animals, obstacles, dt: float) -> None:
        # [호출→] _desired(조향 목표 계산) → _steer(현재 속도를 그쪽으로 보간)
        self._steer(a, self._desired(a, animals, obstacles), dt)
        a.position += a.velocity * dt   # 속도 × 시간 = 이동(위치 갱신)
        r = a.radius
        top = max(r, self.top_margin)
        # 맵 안으로 고정하고, '벽을 향해 파고드는' 속도 성분은 0 으로 — 벽을 응시하며
        # 멈춰 서거나 벽을 미는 일이 없게 한다(방향 표시는 velocity 를 따르므로 안쪽을 봄).
        # [문법] a, b = x, y : 두 값을 한 줄에 동시 대입(튜플 언패킹).
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
        # [문법] v.lerp(target, t) : 현재 v 와 target 사이를 비율 t(0~1)로 선형 보간.
        #        보간 비율 1-exp(-agility·dt) 는 프레임 간격이 달라도 같은 '반응 속도'를 보장한다.
        a.velocity = a.velocity.lerp(target, 1.0 - math.exp(-a.agility * dt))

    def _desired(self, a, animals, obstacles) -> Vector2:
        """desired_velocity + 세 조향력을 합쳐 이번 프레임의 '목표 속도'를 만든다."""
        sp = max(a.speed, 1.0)                # [변수] 이 동물의 기준 속도(0 방지)
        target = Vector2(a.desired_velocity)  # AI 가 정한 '가고 싶은 속도'에서 출발
        target += self._sep(a, animals) * sp           # ① 분리
        target += self._avoid(a, obstacles) * sp * 1.4 # ② 회피(조금 더 세게)
        # 허기가 최고 속도에 반영된다. 스태미나 효과는 speed 프로퍼티에서 처리.
        # [문법] hasattr(x, "이름") : x 에 그 속성/메서드가 있으면 True(없는 종도 안전하게 처리).
        hunger = a.hunger_speed_factor() if hasattr(a, "hunger_speed_factor") else 1.0
        cap = max(sp, a.desired_velocity.length()) * hunger   # [변수] 속도 상한
        if target.length() > cap:
            target.scale_to_length(cap)       # 상한을 넘으면 방향은 두고 길이만 줄임
        # 가장자리 힘은 speed cap 바깥에서 더해야 desired_velocity 에 묻히지 않고 확실히 작동한다.
        # cap 안에 넣으면 desired_velocity 와 합산 후 같은 크기로 잘려 벽 회피력이 사실상 0이 된다.
        target += self._edges(a) * sp * 2.2   # ③ 가장자리(상한 '밖'에서 더함 — 의도된 설계)
        return target

    @staticmethod
    def _repel(here: Vector2, there: Vector2, reach: float) -> Vector2:
        """here 가 there 로부터 reach 안이면, 멀어지는 방향으로 '가까울수록 센' 단위힘."""
        # [문법] @staticmethod : self 를 받지 않는 '도구' 메서드. 인스턴스 상태와 무관한 순수 계산.
        d = here - there
        dist = d.length()
        if 1e-6 < dist < reach:               # [문법] a < x < b : 파이썬은 부등식 연쇄를 지원
            return d / dist * (1.0 - dist / reach)   # 단위벡터 × (가까울수록 1에 가까운 세기)
        return Vector2()                      # 범위 밖/겹침이면 힘 없음(영벡터)

    def _sep(self, a, animals) -> Vector2:
        """① 분리: 가까운 다른 동물들에게서 멀어지는 힘의 합."""
        # 지금 쫓는/상호작용하는 대상에게선 분리하지 않는다 → 포식자가 먹이에 끝까지 붙는다.
        target = getattr(a, "interaction_target", None)
        force = Vector2()
        for o in animals:
            if o is not a and o is not target:   # 자기 자신·상호작용 대상은 제외
                force += self._repel(a.position, o.position,
                                     (a.radius + o.radius) * self.SEP_RANGE)
        return force

    def _avoid(self, a, obstacles) -> Vector2:
        """② 회피: 나무·물가 등 벽에서 미리 비껴 가는 힘의 합."""
        force = Vector2()
        for pos, br in obstacles:   # br = 벽이 막는 반지름
            force += self._repel(a.position, pos, a.radius + br + self.AVOID_PAD)
        return force

    def _edges(self, a) -> Vector2:
        """③ 가장자리: 맵 끝에 가까우면 안쪽으로 미는 힘."""
        force, r, m = Vector2(), a.radius, self.EDGE_PAD
        top = max(r, self.top_margin)
        if a.position.x < r + m:                                   # 왼쪽 가까움 → 오른쪽으로
            force.x += 1.0 - (a.position.x - r) / m
        elif a.position.x > self.width - r - m:                    # 오른쪽 가까움 → 왼쪽으로
            force.x -= 1.0 - (self.width - r - a.position.x) / m
        if a.position.y < top + m:                                 # 위쪽 가까움 → 아래로
            force.y += 1.0 - (a.position.y - top) / m
        elif a.position.y > self.height - m:                       # 아래쪽 가까움 → 위로
            force.y -= 1.0 - (self.height - a.position.y) / m
        return force

    # ── 잔여 겹침 해결: 위치 분리 + 겹치는 방향 속도 성분 감쇠 ─────────
    def _separate(self, animals, obstacles) -> None:
        """조향으로도 남은 미세 겹침을 '위치'를 직접 밀어 푼다(속도는 거의 안 죽임)."""
        # [←호출] update() 끝.
        for _ in range(2):   # 2번 반복하면 대부분의 겹침이 안정적으로 풀린다
            # [문법] enumerate(목록) : (인덱스 i, 값 a) 를 함께 돈다.
            for i, a in enumerate(animals):
                if not a.solid:   # 충돌 대상이 아니면 건너뜀
                    continue
                # [문법] animals[i+1:] : i 다음부터 끝까지. 같은 쌍을 두 번 비교하지 않게 한다.
                for b in animals[i + 1:]:
                    if not b.solid:
                        continue
                    d = b.position - a.position
                    dist = d.length()
                    overlap = a.radius + b.radius - dist   # 양수면 둘이 겹친 정도
                    if dist > 1e-6 and overlap > 0:
                        push = d / dist                    # a→b 방향 단위벡터
                        a.position -= push * (overlap * 0.5)   # 둘을 절반씩 반대로 밀어 떼어 놓음
                        b.position += push * (overlap * 0.5)
                        # 서로를 향해 접근 중인 속도 성분을 흡수해 다음 프레임에 다시 겹치는 진동을 막는다.
                        v_rel = b.velocity - a.velocity     # 상대 속도
                        v_along = v_rel.dot(push)           # [문법] dot=내적: push 방향 성분 크기
                        if v_along < 0:                     # 서로 다가오는 중이면
                            impulse = push * (v_along * 0.5)
                            a.velocity += impulse
                            b.velocity -= impulse
                for pos, br in obstacles:    # 구조물은 통과 불가 — 밖으로 밀고 파고드는 속도만 제거
                    d = a.position - pos
                    dist = d.length()
                    md = a.radius + br
                    if dist <= 1e-6:
                        a.position = pos + Vector2(md, 0)   # 정확히 겹치면 임의 방향으로 밀어냄
                    elif dist < md:
                        n = d / dist
                        a.position = pos + n * md           # 벽 표면으로 밀어냄
                        vin = a.velocity.dot(n)
                        if vin < 0:                 # 벽으로 파고드는 성분만 제거 → 접선 미끄러짐만 남김
                            a.velocity -= n * vin

    # ── 지형 효과(은신·갈증 해소 등) — 이동이 아니라 '원 안 효과' 적용 ──
    def apply_terrain_effects(self, entities, terrains) -> None:
        """동굴·호숫가처럼 '원 안에 들어오면 효과'를 주는 지형을 적용한다."""
        # [←호출] world.update() 4단계(physics.update 직후).
        for entity in entities:
            if not entity.alive:
                continue
            for terrain in terrains:
                # Plain(배경)은 효과가 없으니 건너뛰고, 원 안에 들었으면 효과를 준다.
                if terrain.name != "Plain" and terrain.contains(entity):
                    terrain.give_effect(entity)   # [호출→] Cave/LakeSide.give_effect
