# =============================================================================
# entities/entity.py — 모든 사물의 공통 뿌리 Entity (역할: 공통 상태 + 표시 데이터)
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
#
#  [실행 흐름에서의 위치]
#    이 클래스는 직접 만들어지지 않고, Animal/Plant/Resource/Terrain 이 상속해 쓴다.
#    각 종 객체가 만들어질 때(seed 단계) super().__init__() 으로 여기 __init__ 이 먼저 실행된다.
#    move_toward/stop 등은 동물 AI(behave)가 '가고 싶은 방향'을 적을 때 호출되고,
#    그 결과(desired_velocity)를 physics 가 다음 단계에서 실제 이동으로 바꾼다.
# =============================================================================
# [문법] from itertools import count : 1,2,3,... 무한히 증가하는 카운터를 만드는 도구.
from itertools import count

from pygame.math import Vector2

# [변수] _ENTITY_IDS : 1부터 시작하는 전역 ID 발급기. 모든 Entity 가 만들어질 때마다 하나씩 꺼내 쓴다.
#        (next() 를 부를 때마다 1, 2, 3, ... 을 돌려줘 개체마다 고유 번호를 준다)
_ENTITY_IDS = count(1)


class Entity:
    # [문법] def __init__(self, ...) : 생성자. Entity(...) 로 객체를 만들 때 자동 호출된다.
    #        기본값(kind="entity" 등)이 있는 인자는 자식이 필요한 것만 골라 넘긴다.
    def __init__(self, name, position, radius, color, kind="entity",
                 solid=True, render_shape="square", layer=0, draw_scale=1.0):
        # [←호출] 각 자식 클래스의 __init__ 안에서 super().__init__(...) 으로 호출된다.
        self.id = next(_ENTITY_IDS)           # [변수] 이 개체의 고유 번호(클릭 선택·블랙리스트 등에 사용)
        self.name = name                      # [변수] 종 이름(예: "Lion"). 스프라이트 파일·표시에 사용
        self.position = Vector2(position)     # [변수] 맵 좌표(Vector2). Vector2(position)로 복사본을 만든다
        self.velocity = Vector2()             # [변수] 현재 '실제' 속도(physics 가 갱신). 처음엔 0
        self.desired_velocity = Vector2()     # [변수] '가고 싶은' 속도(AI 가 적고 physics 가 따라감). 처음엔 0
        self.radius = radius                  # [변수] 충돌·상호작용 기준 크기(표시 크기와 별개)
        self.color = color                    # [변수] (R,G,B) — 스프라이트 이미지가 없을 때 표시색
        self.kind = kind                      # [변수] 종류 "animal"/"plant"/"resource"/"terrain"
        self.alive = True                     # [변수] 살아있는가(False면 시뮬·렌더에서 제외)
        self.solid = solid                    # [변수] True면 충돌 분리 대상(동물=True, 풀=False)
        self.render_shape = render_shape      # [변수] gui 표시 모양 힌트(스프라이트 없을 때)
        self.layer = layer                    # [변수] 그리는 순서(작을수록 아래에 깔림)
        self.draw_scale = draw_scale          # [변수] 스프라이트 크기 보정 배율(미어캣 거대화 등에 사용)
        self.action_text = ""                 # [변수] 현재 행동 문자열(예 "hunt"). 머리 위 표시·애니메이션 선택에 사용
        self.agility = 6.0                    # [변수] steering 반응 속도(클수록 빠르게 방향 전환)

    # ── 시간 변화(서브클래스가 오버라이드) ─────────────────────────────
    def update(self, world, dt):
        """매 프레임 변화의 진입점. 기본은 아무것도 안 함 — 자식(Animal/Plant 등)이 새로 정의."""
        # [문법] '오버라이드(override)' : 자식 클래스가 같은 이름 메서드를 다시 정의해 동작을 바꾸는 것.
        return None

    # ── 기하 질의(Vector2 에 위임) ───────────────────────────────────────
    def distance_to(self, other):
        """다른 개체까지의 직선 거리. 실제 계산은 Vector2 에 맡긴다."""
        return self.position.distance_to(other.position)

    def is_near(self, target, range_value):
        """target 이 range_value 안에 있으면 True."""
        return self.distance_to(target) <= range_value

    # ── 이동 의도(desired_velocity 만 설정, 실제 가감속은 physics 의 steering) ──
    def move_toward(self, target, speed):
        """target 위치 쪽으로 가고 싶다고 표시한다."""
        # [←호출] 동물 AI(예: hunt, search_food)에서 먹이·물 쪽으로 갈 때.
        self.desired_velocity = self._toward(target, speed)

    def move_away_from(self, target, speed):
        """target 위치 반대쪽으로 가고 싶다고 표시한다."""
        # [←호출] 도주·회피(예: 사자가 코끼리 피하기)에서.
        self.desired_velocity = self._toward(target, speed) * -1.0   # 방향을 반대로 뒤집음

    def move(self, direction, speed=None):
        """주어진 방향(Vector2)으로 가고 싶다고 표시한다."""
        speed = self.speed if speed is None else speed   # speed 를 안 주면 자기 기본 속도 사용
        # [문법] length_squared() < 1e-9 : 길이가 사실상 0인지 검사(제곱근 없이 빨라 0 나눗셈을 피함).
        if direction.length_squared() < 1e-9:
            self.desired_velocity = Vector2()
        else:
            self.desired_velocity = direction.normalize() * speed   # 방향을 길이1로 만든 뒤 속도를 곱함

    def stop(self):
        """가고 싶은 속도를 0 으로 — physics 가 부드럽게 멈춰 세운다."""
        self.desired_velocity = Vector2()

    def _toward(self, target, speed):
        """self → target 단위벡터 × speed (길이 0 이면 영벡터). 내부 헬퍼."""
        delta = target - self.position           # 나에게서 목표로 향하는 벡터
        if delta.length_squared() < 1e-9:
            return Vector2()
        return delta.normalize() * speed         # 방향(길이1) × 속도

    def status(self):
        """디버그·헤드리스 출력용 한 줄 상태 문자열."""
        state = "alive" if self.alive else "dead"
        # [문법] {self.position.x:.0f} : 소수점 0자리(정수처럼) 출력.
        return f"{self.name}: {state} ({self.position.x:.0f}, {self.position.y:.0f})"
