# =============================================================================
# entities/base.py — 모든 사물의 공통 뿌리 Entity (역할: 공통 상태 + 표시 데이터)
#
# 동물·식물·자원·지형이 공통으로 갖는 것:
#   - 좌표(position)·속도(velocity)·충돌 크기(radius)
#   - 생사(alive)·충돌 여부(solid)·종류(kind)
#   - 화면 표시 정보(color, render_shape, draw_scale, layer, action_text)
#   - 시간에 따른 변화 진입점 update()
# gui 는 여기 '표시 데이터'만 읽어 그리며, Entity 는 pygame 의 '벡터'만 빌려 쓴다.
#
# [이동 모델 — 핵심 변경]
#   예전: move_* 가 velocity 를 '즉시' 바꿔, 매 결정마다 방향이 툭툭 꺾였다.
#   지금: move_* 는 '원하는 속도'(desired_velocity)만 적어 둔다. 실제 velocity 는
#         physics 가 매 프레임 desired 쪽으로 '부드럽게 보간(steering)'한다.
#         → 직선+급회전 대신, 완만하게 휘어지는 자연스러운 움직임이 나온다.
# 좌표·거리 같은 벡터 연산은 pygame.math.Vector2 에 위임한다(중복 구현 제거).
# =============================================================================
from itertools import count

from pygame.math import Vector2

_ENTITY_IDS = count(1)


class Entity:
    def __init__(self, name, position, radius, color, kind="entity",
                 solid=True, render_shape="square", layer=0, draw_scale=1.0):
        self.id = next(_ENTITY_IDS)
        self.name = name
        self.position = Vector2(position)     # Vector2 (맵 좌표)
        self.velocity = Vector2()             # Vector2 (현재 실제 속도)
        self.desired_velocity = Vector2()     # Vector2 (가고 싶은 속도 — steering 목표)
        self.radius = radius                  # 충돌·상호작용 기준 크기
        self.color = color                    # (R,G,B) — 스프라이트 없을 때 표시색
        self.kind = kind                      # "animal"/"plant"/"resource"/"terrain"
        self.alive = True
        self.solid = solid                    # True면 충돌 분리 대상
        self.render_shape = render_shape      # gui 표시 모양 힌트
        self.layer = layer                    # 그리는 순서(작을수록 아래)
        self.draw_scale = draw_scale          # 스프라이트 크기 보정 배율
        self.action_text = ""                 # 현재 행동(머리 위 표시용)
        self.agility = 6.0                    # steering 반응 속도(클수록 빠르게 방향 전환)

    # ── 시간 변화(서브클래스가 오버라이드) ─────────────────────────────
    def update(self, world, dt):
        return None

    # ── 기하 질의(Vector2 에 위임) ───────────────────────────────────────
    def distance_to(self, other):
        return self.position.distance_to(other.position)

    def is_near(self, target, range_value):
        return self.distance_to(target) <= range_value

    # ── 이동 의도(desired_velocity 만 설정, 실제 가감속은 physics 의 steering) ──
    def move_toward(self, target, speed):
        """target 위치 쪽으로 가고 싶다고 표시한다."""
        self.desired_velocity = self._toward(target, speed)

    def move_away_from(self, target, speed):
        """target 위치 반대쪽으로 가고 싶다고 표시한다."""
        self.desired_velocity = self._toward(target, speed) * -1.0

    def move(self, direction, speed=None):
        """주어진 방향(Vector2)으로 가고 싶다고 표시한다."""
        speed = self.speed if speed is None else speed
        if direction.length_squared() < 1e-9:
            self.desired_velocity = Vector2()
        else:
            self.desired_velocity = direction.normalize() * speed

    def stop(self):
        """가고 싶은 속도를 0 으로 — physics 가 부드럽게 멈춰 세운다."""
        self.desired_velocity = Vector2()

    def _toward(self, target, speed):
        """self → target 단위벡터 × speed (길이 0 이면 영벡터). 내부 헬퍼."""
        delta = target - self.position
        if delta.length_squared() < 1e-9:
            return Vector2()
        return delta.normalize() * speed

    def status(self):
        state = "alive" if self.alive else "dead"
        return f"{self.name}: {state} ({self.position.x:.0f}, {self.position.y:.0f})"
