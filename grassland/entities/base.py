# =============================================================================
# entities/base.py — 모든 사물의 공통 뿌리 Entity (역할: 공통 상태 + 표시 데이터)
#
# 동물·식물·자원·지형이 공통으로 갖는 것:
#   - 좌표(position)·속도(velocity)·충돌 크기(radius)
#   - 생사(alive)·충돌 여부(solid)·종류(kind)
#   - 화면 표시 정보(color, render_shape, draw_scale, layer, action_text)
#   - 시간에 따른 변화 진입점 update()
# gui 는 여기 '표시 데이터'만 읽어 그리며, Entity 는 pygame 을 모른다.
# 거리·근접 같은 기하 질의는 geometry(Vec2)에 위임한다(중복 계산 방지).
# =============================================================================
from itertools import count

from grassland.geometry import Vec2

_ENTITY_IDS = count(1)


class Entity:
    def __init__(self, name, position, radius, color, kind="entity",
                 solid=True, render_shape="square", layer=0, draw_scale=1.0):
        self.id = next(_ENTITY_IDS)
        self.name = name
        self.position = position          # Vec2 (맵 좌표)
        self.velocity = Vec2()            # Vec2 (이동 속도)
        self.radius = radius              # 충돌·상호작용 기준 크기
        self.color = color                # (R,G,B) — 스프라이트 없을 때 표시색
        self.kind = kind                  # "animal"/"plant"/"resource"/"terrain"
        self.alive = True
        self.solid = solid                # True면 충돌 분리 대상
        self.render_shape = render_shape  # gui 표시 모양 힌트
        self.layer = layer                # 그리는 순서(작을수록 아래)
        self.draw_scale = draw_scale      # 스프라이트 크기 보정 배율
        self.action_text = ""             # 현재 행동(머리 위 표시용)

    # ── 시간 변화(서브클래스가 오버라이드) ───────────────────────────────
    def update(self, world, dt):
        return None

    # ── 기하 질의(geometry 에 위임) ──────────────────────────────────────
    def distance_to(self, other):
        return self.position.distance_to(other.position)

    def is_near(self, target, range_value):
        return self.distance_to(target) <= range_value

    # ── 이동 의도(속도만 설정, 실제 이동은 physics 가 수행) ───────────────
    def move_toward(self, target, speed):
        self.velocity = (target - self.position).normalized() * speed

    def move_away_from(self, target, speed):
        self.velocity = (self.position - target).normalized() * speed

    def stop(self):
        self.velocity = Vec2()

    def status(self):
        state = "alive" if self.alive else "dead"
        return f"{self.name}: {state} ({self.position.x:.0f}, {self.position.y:.0f})"
