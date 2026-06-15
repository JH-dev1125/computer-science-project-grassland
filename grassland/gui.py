# =============================================================================
# gui.py — 화면 표시 전용 (역할: 그리기 + 카메라). 게임 로직 없음.
#
# world 를 '읽기만' 해서 화면에 그린다. Entity 의 표시 데이터(color, radius,
# action_text, health)만 사용하고, 시뮬레이션 상태를 바꾸지 않는다(카메라 제외).
#
# [버그 수정 메모]
#  - 하늘 스프라이트: 위쪽에 가로 밴드를 붙이던 방식을 제거.
#    탑다운 맵에 '하늘 띠'는 어색하고 상단 UI 패널과 겹쳤다.
#    → 날씨는 화면 전체에 은은한 '틴트(반투명 색)'로 표현(WEATHER_TINT).
#  - GUI 겹침: 날씨 틴트를 동물 위·UI 패널 아래 순서로 그려 패널을 가리지 않게 함.
#  - terrain 겹침: 지형은 가장 아래 레이어에 먼저 그리고, 배경 Plain 은 fill 로만
#    처리(개체로 그리지 않음). 지형 좌표도 world 에서 서로 멀리 배치.
# =============================================================================
#
#  [실행 흐름에서의 위치 — 프로그램의 '심장 박동'이 여기 있다]
#    app.run() 이 GrasslandApp(world).run() 으로 이 클래스를 띄운다.
#    run() 의 while 루프가 매 프레임:
#        ① 입력 처리(키·마우스)  ②  world.update(dt)  (시뮬 한 칸)  ③ draw()  (화면 그림)
#    → 즉 'main.py → app.run → 여기 run() 루프 → 매 프레임 world.update + draw' 가 큰 줄기다.
#    이 파일 자체는 시뮬 상태를 바꾸지 않고 'world 를 읽어 그리기'만 한다(카메라 이동 제외).
# =============================================================================
import math
import pygame   # [문법] 게임 라이브러리. 창·이미지·도형·폰트·이벤트를 담당.

from grassland.config import (
    BACKGROUND_COLOR, FPS, GRID_COLOR, MIN_SCREEN_HEIGHT, MIN_SCREEN_WIDTH,
    PANEL_BORDER, PANEL_COLOR, SCREEN_HEIGHT, SCREEN_WIDTH, SKY_BAND_HEIGHT,
    SPRITE_DISPLAY_DEFAULT, SPRITE_DISPLAY_SIZE, TEXT_COLOR, WEATHER_TINT,
)
from grassland.sprites import (    # 이미지 로딩·캐시 함수들(sprites.py)
    get_sprite, trimmed, get_background, get_sky_image,
    get_weather_icon, sprite_exists, scale_longest,
)
from pygame.math import Vector2


class GrasslandApp:
    # [문법] 클래스 변수(상수) — 모든 인스턴스가 공유하는 설정값.
    SPEED_STEPS = (0.25, 0.5, 1.0, 2.0, 4.0)   # [변수] 배속 단계(← → 키로 이동)
    DEFAULT_SPEED = 0.5                        # [변수] 시작 배속
    WEATHER_ORDER = ("sunny", "cloudy", "rain", "drought")  # [변수] D 키로 순환할 날씨 순서

    def __init__(self, world):
        # [←호출] app.run() 의 GrasslandApp(world) 에서. (흐름 4)
        pygame.init()                                   # pygame 전체 초기화
        pygame.display.set_caption("와글와글 초원 생태계")   # 창 제목
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        # [변수] screen : 실제로 그림을 그리는 창 표면. RESIZABLE = 크기 조절 가능.
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()        # [변수] FPS 를 맞춰 주는 시계
        self.world = world                      # [변수] 그릴 대상(시뮬 상태 전체)
        # 세로는 고정(항상 0), 가로만 스크롤. 초원은 하늘 띠(field_top) 아래부터 그린다.
        self.camera = Vector2(220, 0)           # [변수] 카메라 위치(가로 스크롤만 사용)
        self.field_top = SKY_BAND_HEIGHT        # [변수] 땅 그리기 시작 y(이 위는 하늘)
        self.dragging = False                   # [변수] 마우스로 카메라를 끄는 중인가
        self._press_pos = None       # [변수] 클릭 vs 드래그 구분용(눌렀을 때 화면 좌표)
        self.selected = None         # [변수] 클릭으로 선택된 몹(없으면 None)
        self.clicked_point = None    # [변수] 맵의 빈 곳을 클릭했을 때의 월드 좌표(Vector2 또는 None)
        self.info_collapsed = False  # [변수] 좌하단 정보 패널 접힘 여부
        self.info_toggle_rect = None  # [변수] 패널 접기/펼치기 버튼 영역(draw_ui 가 매 프레임 갱신)
        self.weather_icon_rect = None  # [변수] 날씨 아이콘 영역(툴팁 판정용)
        self.paused = False                     # [변수] 일시정지 상태
        # [변수] speed_index : 현재 배속이 SPEED_STEPS 의 몇 번째인지. .index() 로 초기 위치를 찾음.
        self.speed_index = self.SPEED_STEPS.index(self.DEFAULT_SPEED)
        self.font = self._font(17)              # [변수] 보통 글꼴
        self.small_font = self._font(14)        # [변수] 작은 글꼴
        self.title_font = self._font(22, bold=True)  # [변수] 제목용 굵은 글꼴
        self._init_sky()                        # [호출→] 구름·해·달·비 입자 준비

    def _font(self, size, bold=False):
        """시스템에 있는 한글 글꼴을 우선순위대로 찾아 돌려준다(없으면 기본 글꼴)."""
        for name in ("malgungothic", "malgun gothic", "nanumgothic", "segoeui", "arial"):
            font = pygame.font.SysFont(name, size, bold=bold)
            if font is not None:
                return font
        return pygame.font.Font(None, size)

    # ── 메인 루프 ────────────────────────────────────────────────────────
    def run(self):
        """프로그램이 켜져 있는 동안 끝없이 도는 '게임 루프'. 창을 닫을 때까지 반복."""
        # [←호출] app.run() 의 GrasslandApp(world).run() 에서.  (흐름 4 → 매 프레임 흐름 B)
        running = True
        while running:
            # [변수] raw_dt : 지난 프레임 이후 실제 흐른 시간(초). tick(FPS) 가 FPS 를 맞춘다.
            raw_dt = self.clock.tick(FPS) / 1000.0
            # [변수] sim_dt : 시뮬레이션에 적용할 시간. 일시정지면 0, 아니면 배속을 곱함.
            sim_dt = 0.0 if self.paused else raw_dt * self.time_scale
            self.dt = sim_dt                    # 그리기(애니메이션)에서도 참조
            # ── 1) 입력 처리: 키보드·마우스 이벤트를 하나씩 꺼내 처리 ──────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:           # 창 닫기 버튼
                    running = False
                elif event.type == pygame.KEYDOWN:      # 키를 눌렀을 때
                    if event.key == pygame.K_r:
                        self._restart()                 # R: 재시작
                    elif event.key == pygame.K_SPACE and not self.world.environment.ended:
                        self.paused = not self.paused   # Space: 일시정지 토글
                    elif event.key == pygame.K_RIGHT:
                        self._change_speed(1)           # →: 배속 증가
                    elif event.key == pygame.K_LEFT:
                        self._change_speed(-1)          # ←: 배속 감소
                    elif event.key == pygame.K_d and not self.world.environment.ended:
                        self._cycle_weather()           # D: 날씨 강제 전환
                    elif event.key == pygame.K_e and not self.world.environment.ended:
                        self._end_game()                # E: 미어캣 엔딩 강제 발동
                    elif self.world.environment.ended and event.key in (pygame.K_y, pygame.K_RETURN):
                        self._restart()                 # 종료 화면에서 Y/Enter: 재시작
                    elif self.world.environment.ended and event.key in (pygame.K_n, pygame.K_ESCAPE):
                        running = False                 # 종료 화면에서 N/Esc: 끝
                elif event.type == pygame.VIDEORESIZE:
                    self.resize(event.w, event.h)       # 창 크기 변경
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.dragging = True
                    self._press_pos = event.pos         # 누른 위치 기억(클릭/드래그 구분용)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.dragging = False
                    # 누른 자리와 뗀 자리가 거의 같으면 '드래그'가 아니라 '클릭' →
                    # 그 위치의 몹을 선택해 속성 패널에 띄운다.
                    if self._press_pos is not None:
                        dx = event.pos[0] - self._press_pos[0]
                        dy = event.pos[1] - self._press_pos[1]
                        if dx * dx + dy * dy <= 25:      # 이동 거리² ≤ 25 → 클릭으로 간주
                            if self.info_toggle_rect is not None and self.info_toggle_rect.collidepoint(event.pos):
                                self.info_collapsed = not self.info_collapsed   # 패널 접기 버튼
                            else:
                                self.handle_click(event.pos)   # [호출→] 개체 선택
                    self._press_pos = None
                elif event.type == pygame.MOUSEMOTION and self.dragging:
                    self.camera.x -= event.rel[0]   # 가로만 이동(세로 고정) — 드래그로 스크롤
                    self.clamp_camera()
            # ── 2) 시뮬레이션 한 칸 진행 (일시정지·종료가 아니면) ─────────────
            # [호출→] world.update(sim_dt) : 환경→식물→동물→물리→후처리 (흐름 B의 핵심)
            if not self.world.environment.ended and sim_dt > 0.0:
                self.world.update(sim_dt)
            self.update_sky(0.0 if self.paused else raw_dt)   # 구름 흐름 갱신
            # ── 3) 화면 그리기 ───────────────────────────────────────────
            self.draw()                          # [호출→] draw()
        pygame.quit()                            # 루프 종료 → 창 닫기

    @property
    def time_scale(self):
        """현재 배속(읽을 때마다 speed_index 로 SPEED_STEPS 에서 꺼냄)."""
        return self.SPEED_STEPS[self.speed_index]

    def _restart(self):
        """R 키: 맵을 새로 만들어 처음부터 다시 시작."""
        from grassland.world import World      # [문법] 함수 안 지연 import(순환 import 방지)
        self.world = World.seed_default()       # [호출→] 새 월드 생성(흐름 A)
        self.camera = Vector2(220, 0)
        self.selected = None
        self.clicked_point = None
        self.paused = False
        self.speed_index = self.SPEED_STEPS.index(self.DEFAULT_SPEED)
        self._init_sky()

    def _change_speed(self, step):
        """배속 단계를 step 만큼 이동(범위를 벗어나지 않게 clamp)."""
        self.speed_index = max(0, min(len(self.SPEED_STEPS) - 1,
                                      self.speed_index + step))

    def _cycle_weather(self):
        """D 키: 날씨를 WEATHER_ORDER 순서로 다음 것으로 강제 전환."""
        env = self.world.environment
        try:
            i = self.WEATHER_ORDER.index(env.weather)   # 현재 날씨의 위치
        except ValueError:
            i = -1                                       # 목록에 없으면 -1(다음에 0이 됨)
        env.weather = self.WEATHER_ORDER[(i + 1) % len(self.WEATHER_ORDER)]   # 순환
        env.change_temp()                                # 새 날씨에 맞는 온도
        env._weather_hours = 0.0                         # 자동 변경 타이머 리셋

    def _end_game(self):
        """E 키: 날짜를 엔딩일로 점프시켜 미어캣 엔딩을 강제 발동."""
        from grassland.config import MEERKAT_ENDING_DAY
        self.world.environment.day = MEERKAT_ENDING_DAY

    # ── 카메라 ───────────────────────────────────────────────────────────
    def clamp_camera(self):
        """카메라가 맵 밖으로 나가지 않게 가로 범위를 가둔다(세로는 0 고정)."""
        self.camera.x = max(0, min(self.camera.x, max(0, self.world.width - self.screen_width)))
        self.camera.y = 0   # 세로 고정

    def resize(self, width, height):
        """창 크기가 바뀌면 최소 크기를 보장하며 표면을 다시 만든다."""
        self.screen_width = max(MIN_SCREEN_WIDTH, width)
        self.screen_height = max(MIN_SCREEN_HEIGHT, height)
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.clamp_camera()

    def world_to_screen(self, position):
        """월드 좌표 → 화면 좌표. (모든 그리기가 이걸로 위치를 변환한다)"""
        # 세로는 고정 → 월드 y 에 field_top 만 더한다(하늘 띠 아래부터 시작).
        return int(position.x - self.camera.x), int(position.y + self.field_top)

    def visible(self, entity, margin=120):
        """이 개체가 화면 안(여유 margin 포함)에 보이는가 — 안 보이면 안 그려 성능 절약."""
        x, y = self.world_to_screen(entity.position)
        return -margin <= x <= self.screen_width + margin and \
               -margin <= y <= self.screen_height + margin

    # ── 스프라이트(이미지) 그리기 ────────────────────────────────────────
    def display_size(self, entity):
        """이 개체를 화면에 얼마나 크게(긴 변, px) 그릴지 — config 의 현실적 크기비 표에서."""
        base = SPRITE_DISPLAY_SIZE.get(entity.name, SPRITE_DISPLAY_DEFAULT)
        return int(base * entity.draw_scale)   # draw_scale: 미어캣 거대화 등 배율 반영

    # ── 행동 애니메이션 설정 ──────────────────────────────────────────────
    # 동물 name → { "actions": {action_text → 상태},  "states": {상태 → (프레임목록, 프레임당 초)} }
    #   - 프레임목록: 파일이 없는 프레임은 자동으로 걸러지고, 모두 없으면 idle(<name>) 로 폴백.
    #   - 프레임당 초: 클수록 천천히 바뀐다(걷기 0.30s ≈ 자연스러운 속보, 질주는 더 빠르게).
    #   - 같은 동물의 모든 프레임은 '같은 축척'으로 그려진다(sprites.trimmed 가 여백을 잘라 정규화).
    #   - 동물은 idle 그림을 '걷기 0프레임(walk0)'으로 보고 walk1 과 번갈아 걷는다(독수리 제외).
    # 크기 정규화 모드(blit_sprite): 기본 geom(면적, 자세가 달라도 덩치 일정).
    # 독수리만 height(날갯짓 때 가로폭만 변하도록).
    NORM_MODE = {"Bald_Eagle": "height"}   # [변수] 종별 크기 정규화 기준(없으면 geom)

    # [변수] ANIMATIONS : 동물별 '행동→상태→프레임' 표. _animation() 이 이걸 보고 그릴 프레임을 고른다.
    ANIMATIONS = {
        "Lion": {
            "actions": {"hunt": "hunt", "attack": "hunt", "ambush": "hunt",
                        "roar": "roar", "hide": "hide",
                        "avoid": "walk", "return": "walk", "stalk": "walk",
                        "eat": "idle", "search_food": "walk"},
            "states": {"walk": (["lion", "lion_walk1"], 0.36),
                       "hunt": (["lion_hunt1", "lion_hunt2"], 0.28),
                       "roar": (["lion_roar"], 1.0), "hide": (["lion_hide"], 1.0),
                       "idle": (["lion"], 1.0)},
        },
        "Hyena": {
            "actions": {"hunt": "hunt", "attack": "hunt", "ambush": "hunt",
                        "steal": "steal",
                        "avoid": "walk", "return": "walk", "stalk": "walk",
                        "eat": "idle", "search_food": "walk"},
            "states": {"walk": (["hyena", "hyena_walk1"], 0.25),
                       "hunt": (["hyena_hunt1", "hyena_hunt2"], 0.16),
                       "steal": (["hyena_steal_prey"], 1.0), "idle": (["hyena"], 1.0)},
        },
        "Bald_Eagle": {   # 독수리는 idle 대신 날갯짓 두 프레임(fly1↑/fly2↓)을 번갈아 쓴다
            "actions": {"fly": "fly",
                        "swoop": "swoop", "hunt": "swoop", "attack": "swoop",
                        "land": "land", "eat": "land", "search_food": "fly",
                        "avoid": "fly", "water": "fly"},
            "states": {"fly": (["bald_eagle_fly1", "bald_eagle_fly2"], 0.30),
                       "swoop": (["bald_eagle_swoop"], 1.0),
                       "land": (["bald_eagle_land"], 1.0), "idle": (["bald_eagle"], 1.0)},
        },
        "Elephant": {
            "actions": {"stomp": "stomp",
                        "water": "walk", "return": "walk",
                        "eat": "idle", "search_food": "walk"},
            "states": {"walk": (["elephant", "elephant_walk1"], 0.32),
                       "stomp": (["elephant_stomp"], 1.0), "idle": (["elephant"], 1.0)},
        },
        "Gazelle": {
            "actions": {"flee": "flee", "zigzag": "flee",
                        "water": "walk",
                        "eat": "idle", "search_food": "walk"},
            "states": {"walk": (["gazelle", "gazelle_walk1"], 0.34),
                       "flee": (["gazelle_flee", "gazelle_walk1"], 0.20),
                       "idle": (["gazelle"], 1.0)},
        },
        "Zebra": {
            "actions": {"kick": "kick", "flee": "flee", "attack": "kick",
                        "water": "walk",
                        "eat": "idle", "search_food": "walk"},
            "states": {"walk": (["zebra", "zebra_walk1"], 0.24),
                       "flee": (["zebra", "zebra_walk1"], 0.12),
                       "kick": (["zebra_kick"], 1.0), "alert": (["zebra_alert"], 1.0),
                       "idle": (["zebra"], 1.0)},
        },
        "Meerkat": {
            "actions": {"stand": "stand",
                        "hide": "hide", "cave": "cave",
                        "water": "walk", "drink": "walk",
                        "flee": "walk", "hunt": "walk", "boss": "walk",
                        "eat": "idle", "search_food": "walk"},
            "states": {"walk": (["meerkat_walk"], 1.4),
                       "stand": (["meerkat_stand"], 1.4),
                       "cave": (["meerkat_cave"], 1.4),
                       "hide": (["meerkat_hide"], 1.4),
                       "idle": (["meerkat"], 1.0)},
        },
        "Warthog": {
            "actions": {"burrow": "liedown",
                        "water": "walk", "search_food": "walk"},
            "states": {"walk": (["warthog", "warthog_walk1"], 0.28),
                       "liedown": (["warthog_liedown"], 1.0),
                       "idle": (["warthog"], 1.0)},
        },
    }

    def _animation(self, entity):
        """이 동물의 현재 상태에 맞는 (프레임이름 리스트, 프레임당 지속시간[초]).
        action_text → 상태 매핑이 있으면 그걸 쓰고, 없으면 이동속도로 walk/idle 을 고른다.
        실제 파일이 없는 프레임은 제거하고, 하나도 없으면 idle(기본 이미지)로 폴백한다."""
        base = entity.name.lower()              # [변수] 파일 접두어(예: "lion")
        cfg = self.ANIMATIONS.get(entity.name)  # 이 종의 애니메이션 설정(없으면 None)
        action = getattr(entity, "action_text", "") or ""
        state = None
        if cfg:
            state = cfg["actions"].get(action)  # 행동 → 상태 매핑
        if state is None:
            # 매핑이 없으면 이동 속도로 walk/idle 자동 판정
            speed = entity.velocity.length() if hasattr(entity, "velocity") else 0.0
            state = "walk" if speed > 12.0 else "idle"
        if cfg and state in cfg["states"]:
            frames, dur = cfg["states"][state]  # 그 상태의 프레임 목록·속도
        elif state == "walk":
            # 설정에 없는 동물: idle 그림(walk0)과 walk1·walk2 를 번갈아 걷는다.
            frames, dur = ([base, base + "_walk1", base + "_walk2"], 0.26)
        else:
            frames, dur = ([base], 1.0)
        # [문법] [f for f in frames if sprite_exists(f)] or [base] : 실제 존재하는 파일만 남기고,
        #        하나도 없으면 기본 그림(base)으로 폴백.
        frames = [f for f in frames if sprite_exists(f)] or [base]
        return frames, dur, state

    # 특정 (동물, 상태) 조합은 최소 이 시간(초) 유지 후에만 다른 상태로 전환한다.
    # 독수리 swoop·코끼리 stomp 는 순간적으로 트리거되므로 최소 지속 없이는 한 프레임만 보인다.
    _ANIM_MIN_HOLD = {
        ("Bald_Eagle", "swoop"): 0.55,
        ("Elephant",   "stomp"): 0.45,
        ("Meerkat",    "walk"): 0.70,
        ("Meerkat",    "stand"): 0.80,
        ("Meerkat",    "cave"): 0.80,
        ("Meerkat",    "hide"): 0.80,
    }

    def _frame(self, entity, dt):
        """프레임 타이머를 진전시켜 지금 그릴 프레임 이름을 고른다. 상태가 바뀌면
        타이머를 초기화해 새 동작이 처음 프레임부터 자연스럽게 시작되도록 한다.
        _ANIM_MIN_HOLD 에 등록된 상태는 최소 지속 시간을 채우기 전엔 전환되지 않아
        짧게 번쩍이는 것처럼 보이는 현상을 막는다."""
        # [←호출] draw_world 가 동물을 그리기 직전에.
        frames, dur, state = self._animation(entity)
        # [문법] getattr(entity, "_anim_state", None) : 동물 객체에 이 속성이 없으면 None(첫 프레임).
        prev_state = getattr(entity, "_anim_state", None)
        state_hold = getattr(entity, "_anim_state_hold", 0.0)

        if prev_state != state:                 # 상태가 바뀌려 할 때
            min_hold = self._ANIM_MIN_HOLD.get((entity.name, prev_state), 0.0)
            if prev_state is not None and state_hold < min_hold:
                # 아직 최소 유지 시간이 안 됐으므로 이전 상태를 강제 유지
                state = prev_state
                cfg = self.ANIMATIONS.get(entity.name)
                if cfg and state in cfg.get("states", {}):
                    raw_f, dur = cfg["states"][state]
                    base = entity.name.lower()
                    frames = [f for f in raw_f if sprite_exists(f)] or [base]
            else:
                # 상태 전환 허용: 타이머·인덱스 초기화
                entity._anim_state = state
                entity._anim_timer = 0.0
                entity._anim_index = 0
                state_hold = 0.0

        entity._anim_state_hold = state_hold + dt   # 이 상태를 유지한 시간 누적

        if len(frames) <= 1:
            return frames[0]                    # 프레임이 하나면 그대로
        entity._anim_timer = getattr(entity, "_anim_timer", 0.0) + dt
        if entity._anim_timer >= dur:           # 한 프레임 지속시간이 지나면
            entity._anim_timer -= dur
            entity._anim_index = getattr(entity, "_anim_index", 0) + 1   # 다음 프레임으로
        # [문법] index % len : 나머지 연산으로 프레임을 순환(끝나면 처음으로).
        return frames[entity._anim_index % len(frames)]

    def blit_sprite(self, entity, x, y, flip=False, anchor="center", sprite_name=None):
        """entity 의 PNG 를 그린다. anchor="bottom" 이면 '발밑'을 (x,y)에 맞춰 위로 세워
        그린다(오블리크 2.5D — 물체가 바닥을 딛고 서 있는 느낌). "center" 면 바닥에
        누운 것(호숫가·웅덩이). 그린 사각형(Rect)을 돌려준다(체력바 위치 계산용).

        동물은 '내용 기준'(투명 여백을 잘라낸 실제 그림)으로 크기를 맞춰, 프레임마다
        캔버스 크기·여백이 달라도 화면상 동물 크기가 항상 일정하고 발밑이 정확히 맞는다.
        그 외(식물·지형)는 기존 캔버스 기준으로 그린다."""
        base = entity.name.lower()
        name = sprite_name or base              # 줄 그림 이름(애니메이션 프레임 또는 기본)
        size = self.display_size(entity)
        is_animal = getattr(entity, "kind", "") == "animal"
        if is_animal:
            # 독수리는 날개를 폈다 접었다 해 가로폭만 변하므로 '키(height)' 기준으로 맞춰
            # 모든 비행 프레임의 몸통 크기를 똑같이 한다. 나머지 동물은 면적(geom) 기준.
            mode = self.NORM_MODE.get(entity.name, "geom")
            sprite = trimmed(name, size, mode)  # [호출→] sprites.trimmed(여백 잘라 크기 정규화)
            if sprite is None:                      # 프레임 파일이 없으면 idle 로 폴백
                sprite = trimmed(base, size, mode)
        else:
            sprite = get_sprite(name, size)     # 식물·지형은 단순 축소
        if sprite is None:                      # 이미지가 아예 없으면 자주색 점으로 폴백
            r = max(4, size // 5)
            pygame.draw.circle(self.screen, (210, 60, 210), (x, y), r)
            return pygame.Rect(x - r, y - r, 2 * r, 2 * r)
        if flip:
            sprite = pygame.transform.flip(sprite, True, False)   # 좌우 반전(바라보는 방향)
        # 숨은 동물·덤불 안 동물은 반투명으로 그려 '가려진' 느낌
        if getattr(entity, "is_hidden", False) or getattr(entity, "_in_bush", False):
            if not flip:
                sprite = sprite.copy()          # 캐시 원본을 건드리지 않게 복사 후
            sprite.set_alpha(130)               # 투명도 130(0~255)
        if anchor == "bottom":
            rect = sprite.get_rect(midbottom=(x, y))   # 발밑을 (x,y)에 맞춤(서 있는 것)
        else:
            rect = sprite.get_rect(center=(x, y))      # 중심을 (x,y)에 맞춤(누운 것)
        self.screen.blit(sprite, rect)          # 실제로 화면에 그림
        return rect                             # 그린 사각형(체력바·선택고리 위치 계산용)

    def draw_shadow(self, entity, x, y, altitude):
        """떠오른 동물의 발밑(원래 바닥 위치)에 옅은 타원 그림자를 그려 '뜬' 느낌을 강조한다.
        높이 뜰수록 그림자는 작아지고 옅어진다(독수리가 하늘로 멀어지는 인상)."""
        w = max(16, self.display_size(entity) // 2)
        h = max(5, w // 3)
        fade = max(15, 90 - int(altitude * 1.4))   # 높이 뜰수록 옅게
        # [문법] pygame.SRCALPHA : 투명도(알파)를 가진 표면을 만든다.
        shadow = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (20, 20, 20, fade), shadow.get_rect())
        self.screen.blit(shadow, shadow.get_rect(center=(x, y)))

    def _lift(self, entity):
        """이 동물을 그릴 때 발밑 좌표(world_to_screen 결과)에서 위로 들어 올리는
        픽셀 수 — altitude(고도) + bounce(통통 튀는 모션). 그림자는 원래 발밑
        좌표에 그대로 그리지만, 선택 고리·상호작용 선처럼 '동물 자체'를 가리키는
        요소는 이만큼 같이 들어 올려야 화면에 보이는 위치와 어긋나지 않는다."""
        altitude = getattr(entity, "altitude", 0.0)     # 독수리 고도
        bt = getattr(entity, '_bounce_timer', 0.0)      # 바운스 남은 시간
        bd = getattr(entity, '_bounce_duration', 1.0)   # 바운스 총 길이
        bh = getattr(entity, '_bounce_height', 0.0)     # 바운스 최대 높이
        # [문법] sin((1 - bt/bd)·π) : 0→1→0 으로 솟았다 내려오는 포물선 모양의 튐.
        bounce_y = int(math.sin((1.0 - bt / bd) * math.pi) * bh) if bt > 0.0 else 0
        return int(altitude) + bounce_y

    # 바닥에 '누운' 것들(평면). 나머지는 '서 있는' 것으로 보고 발밑을 바닥에 딛는다.
    FLAT_NAMES = ("Lake_Side", "Water_Puddle", "Carcass")

    # ── 그리기(배경그림 → 하늘(해·달·구름) → 깊이정렬된 세계 → UI) ─────────
    def draw(self):
        """한 프레임의 전체 화면을 그린다(뒤→앞 순서로 덮어 그림)."""
        # [←호출] run() 루프 매 프레임.
        self.screen.fill(BACKGROUND_COLOR)        # 그림 없을 때 단색 초록
        has_bg = self.draw_background()           # [호출→] 배경 그림 타일링
        # 하늘(해·달·구름). 배경 그림이 없으면 절차적 하늘(그라데이션+언덕)도 그린다.
        self.draw_sky(procedural=not has_bg)      # [호출→] 하늘
        # 세계: 동물·구조물을 발밑 기준·깊이순으로. 동물은 top_margin 으로 하늘에 못 감.
        self.draw_world()                         # [호출→] 동물·식물·지형
        self.draw_weather_tint()                  # 날씨 틴트
        self.draw_rain()                          # 비 내리는 묘사(비 올 때만)
        self.draw_ui()                            # 정보 패널(좌하단)
        self.draw_selection_panel()                # 선택한 몹의 속성 패널(우상단)
        self.draw_weather_tooltip()               # 날씨 아이콘 호버 툴팁
        pygame.display.flip()                     # 완성된 화면을 실제 모니터에 표시

    def draw_background(self):
        """배경 그림(assets/sprites/background.png)을 가로로 이어붙여(타일링) 깐다.
        세로만 화면 높이에 맞추고 가로 비율은 그대로 둬서, 늘려서 생기는 흐려짐 없이
        선명하게 보이도록 한다. 카메라 위치에 맞춰 필요한 만큼 반복해서 그린다.
        그림이 없으면 False — 이때는 단색 초록 + 절차적 하늘로 폴백."""
        bg = get_background()
        if bg is None:
            return False
        tile, tile_flipped = self._scaled_background(bg)
        tile_w = tile.get_width()
        if tile_w <= 0:
            return False
        cam_x = int(self.camera.x)
        # 카메라 왼쪽 가장자리부터 화면 오른쪽 끝까지 덮도록 타일을 반복해 그린다.
        # 이 배경 그림은 좌우가 매끄럽게 안 이어지는("seamless" 아닌) 그림이라,
        # 한 칸씩 좌우 반전(거울 타일링)해 붙이면 경계의 픽셀이 항상 대칭이 되어
        # 이음매(세로선)가 보이지 않는다.
        start_idx = cam_x // tile_w
        idx = start_idx
        while idx * tile_w < cam_x + self.screen_width:
            img = tile if (idx % 2 == 0) else tile_flipped   # 짝/홀수 칸마다 거울 반전
            self.screen.blit(img, (idx * tile_w - cam_x, 0))
            idx += 1
        return True

    def _scaled_background(self, bg):
        """원본 이미지를 화면 높이에 맞춰 비율 그대로 축소하고(확대와 달리 픽셀이
        깨지지 않음), 거울 타일링용으로 좌우 반전 사본도 함께 만들어 캐시한다."""
        key = int(self.screen_height)
        # 창 높이가 바뀌지 않았으면 캐시 재사용(매 프레임 다시 축소하지 않음)
        if getattr(self, "_bg_key", None) != key:
            bw, bh = bg.get_size()
            scale = key / bh
            new_size = (max(1, round(bw * scale)), key)
            self._bg_scaled = pygame.transform.smoothscale(bg, new_size)
            self._bg_flipped = pygame.transform.flip(self._bg_scaled, True, False)
            self._bg_key = key
        return self._bg_scaled, self._bg_flipped

    def draw_world(self):
        """동물·식물·지형·자원을 '깊이(발밑 y)' 순서로 그려 입체감을 낸다."""
        # [←호출] draw().
        # 1) 바닥에 누운 것(호숫가·물웅덩이·사체)을 먼저, 뒤(작은 y)→앞(큰 y) 순으로.
        flat = []
        for t in self.world.terrains:
            if t.name == "Lake_Side" and self.visible(t, 200):
                flat.append(t)
        for r in self.world.resources:
            if r.alive and r.name in ("Water_Puddle", "Carcass") and self.visible(r):
                flat.append(r)
        # [문법] list.sort(key=lambda e: e.position.y) : 발밑 y가 작은(뒤쪽) 것부터 그리도록 정렬.
        flat.sort(key=lambda e: e.position.y)
        for e in flat:
            x, y = self.world_to_screen(e.position)
            if e.name == "Carcass":
                # amount 비율(0~1)을 0~3 단계로 변환 → carcass0/1/2/3.png 선택
                fraction = e.amount / e.max_amount if e.max_amount > 0 else 0.0
                stage = min(3, max(0, round(fraction * 3)))
                self.blit_sprite(e, x, y, anchor="center", sprite_name=f"carcass{stage}")
            elif e.name == "Lake_Side":
                # 물이 40% 미만으로 줄면 가뭄 이미지로 전환
                fraction = e.water / e.max_water if e.max_water > 0 else 0.0
                sname = "lake_side_drought" if fraction < 0.4 else "lake_side"
                self.blit_sprite(e, x, y, anchor="center", sprite_name=sname)
            else:
                self.blit_sprite(e, x, y, anchor="center")

        # 1.5) 풀(Grass): 작은 장식용 깔개라 깊이 정렬에 끼우면 동물 바로 앞에 있을 때
        #      발밑부터 솟아올라 큰 동물(코끼리)의 몸통을 '뚫고' 가리는 것처럼 보인다.
        #      그래서 풀은 동물·나무보다 항상 먼저(뒤에) 깔아, 몸통을 뚫지 않게 한다.
        #      (덤불 Bush 는 은신처라 깊이 정렬을 유지 → 아래 upright 에 남겨둔다.)
        grasses = [p for p in self.world.alive_plants()
                   if p.name == "Grass" and self.visible(p)]
        grasses.sort(key=lambda e: e.position.y)
        for e in grasses:
            x, y = self.world_to_screen(e.position)
            self.blit_sprite(e, x, y, anchor="bottom")

        # 2) 서 있는 것(동굴·덤불·동물)을 '발밑 y' 기준으로 정렬 — 앞의 것이 뒤를 가린다.
        upright = []
        for t in self.world.terrains:
            if t.name == "Cave" and self.visible(t, 200):
                upright.append(t)
        upright.extend(p for p in self.world.alive_plants()
                       if p.name != "Grass" and self.visible(p))
        upright.extend(a for a in self.world.animals if a.alive and self.visible(a))
        upright.sort(key=lambda e: e.position.y)
        for e in upright:
            x, y = self.world_to_screen(e.position)
            if e.kind == "animal":
                dt = getattr(self, 'dt', 0.0)
                if not hasattr(e, '_flip_cooldown'):
                    e._flip_cooldown = 0.0
                e._flip_cooldown = max(0.0, e._flip_cooldown - dt)
                # 바라보는 방향은 '실제 이동 속도'를 따른다(가고 싶은 방향 X).
                # 벽 근처에서 가장자리 회피로 안쪽으로 꺾이면 얼굴도 안쪽을 향하게 된다.
                dvx = e.velocity.x
                # 쿨다운(0.4초)을 둬 좌우로 빠르게 떨리며 뒤집히는 현상을 막는다.
                if e._flip_cooldown <= 0.0 and getattr(e, "action_text", "") != "cave":
                    if dvx > 8:
                        e.facing_left = False
                        e._flip_cooldown = 0.4
                    elif dvx < -8:
                        e.facing_left = True
                        e._flip_cooldown = 0.4
                altitude = getattr(e, "altitude", 0.0)
                total_lift = self._lift(e)          # 고도+바운스만큼 위로 들어 올림
                # 덤불 안에 있는 동물은 반투명 (is_hidden 있는 동물은 그쪽이 우선)
                # [문법] any(... for ...) : 조건을 만족하는 게 하나라도 있으면 True.
                e._in_bush = any(
                    p.alive and p.name == "Bush"
                    and e.position.distance_to(p.position) < p.radius
                    for p in self.world.plants
                )
                self.draw_shadow(e, x, y, altitude)     # 발밑 그림자(원래 바닥 위치)
                frame = self._frame(e, dt)              # [호출→] 현재 그릴 프레임 이름
                rect = self.blit_sprite(e, x, y - total_lift, flip=not getattr(e, "facing_left", True),
                                        anchor="bottom", sprite_name=frame)
                self.healthbar(e, x, rect.top - 6, self.display_size(e))   # 머리 위 체력바
                if e is self.selected:   # 선택된 몹은 '보이는' 발밑(들어 올려진 위치)에 고리를 그려 표시
                    rw = max(rect.width, 30)
                    ring = pygame.Rect(0, 0, rw + 14, (rw + 14) // 3)
                    ring.center = (x, y - total_lift)
                    pygame.draw.ellipse(self.screen, (255, 230, 90), ring, 3)
            elif e.name == "Cave":
                # 동굴은 "땅에 뚫린 구멍" — 스프라이트 중심을 position 에 맞춰야
                # cave.contains() / move_toward(cave.position) 의 상호작용 위치와 일치한다.
                self.blit_sprite(e, x, y, anchor="center")
            else:
                self.blit_sprite(e, x, y, anchor="bottom")

    def healthbar(self, animal, x, y, width):
        """동물 머리 위 체력바. 비율(0~1)에 따라 길이와 색이 바뀐다(초록→노랑→빨강)."""
        mx = animal.max_health if animal.max_health > 0 else 1.0
        ratio = max(0.0, min(1.0, animal.health / mx))   # 0~1 로 가둔 체력 비율
        w = max(26, min(int(width), 96))      # 종별 크기 반영하되 상·하한
        h = 6
        left, top = x - w // 2, y
        pygame.draw.rect(self.screen, (30, 30, 30), (left - 1, top - 1, w + 2, h + 2),
                         border_radius=2)                       # 테두리
        pygame.draw.rect(self.screen, (92, 74, 66), (left, top, w, h), border_radius=2)  # 빈 칸
        if ratio > 0.5:
            col = (96, 200, 96)               # 초록(건강)
        elif ratio > 0.25:
            col = (232, 200, 72)              # 노랑(주의)
        else:
            col = (222, 84, 72)               # 빨강(위험)
        fw = int(w * ratio)                   # 채워진 길이
        if fw > 0:
            pygame.draw.rect(self.screen, col, (left, top, fw, h), border_radius=2)

    # ── 하늘 띠(상단 고정) — 초원과 독립적으로 항상 화면 위쪽에 떠 있다 ───────
    CLOUD_BASE_W = 150        # [변수] 구름 한 장의 기준 가로폭(px) — 원본 크기와 무관하게 통일
    CLOUD_PARALLAX = 0.35     # [변수] 카메라 이동 대비 구름 이동 비율(1=땅과 같이, 0=화면 고정). 멀리 있는 느낌.

    def _init_sky(self):
        """구름 상태와 그림을 준비. 구름은 '월드' 좌표를 가지고 카메라를 따라(패럴랙스)
        함께 흘러가며, 하늘 띠 안에서 좌우로 떠다닌다.
        cloud1~3.png 가 있으면 그 중 무작위로 골라 쓰고, 없으면 절차적 구름으로 대체."""
        # [←호출] __init__ 와 _restart() 에서.
        import random as _r
        self._sun_img = get_sky_image("sun")
        self._moon_img = get_sky_image("moon")
        # [문법] [im for im in (...) if im is not None] : 존재하는 구름 그림만 모음.
        raw_imgs = [im for im in
                    (get_sky_image("cloud1"), get_sky_image("cloud2"), get_sky_image("cloud3"))
                    if im is not None]
        if not raw_imgs:
            raw_imgs = [self._make_cloud_surface()]   # 그림 없으면 절차적 구름 한 장
        # 원본 이미지 크기가 제각각이라, 가로폭을 기준 크기로 통일해 둔 뒤
        # 개체별로 약간의 변주(scale)만 주어 "너무 크다" 문제를 없앤다.
        self._cloud_imgs = []
        for im in raw_imgs:
            w, h = im.get_size()
            ratio = self.CLOUD_BASE_W / max(1, w)
            new_size = (self.CLOUD_BASE_W, max(1, round(h * ratio)))
            self._cloud_imgs.append(pygame.transform.smoothscale(im, new_size))
        self.clouds = [self._new_cloud() for _ in range(5)]   # 초기 구름 5개
        # 비 입자(화면 좌표). 비 올 때만 그린다. [x, y, 낙하속도]
        self.raindrops = [[_r.uniform(0, self.screen_width), _r.uniform(0, self.screen_height),
                           _r.uniform(650, 950)] for _ in range(240)]

    # 날씨별 목표 구름 수 — 흐림·비엔 하늘을 구름으로 빽빽하게.
    CLOUD_COUNTS = {"sunny": 3, "cloudy": 15, "rain": 20, "drought": 2}

    def _new_cloud(self, x=None):
        """구름 한 덩이의 상태(딕셔너리)를 만든다."""
        import random as _r
        return {
            "x": _r.uniform(0, self.world.width) if x is None else x,   # 월드 x 좌표
            "yf": _r.uniform(0.08, 0.55),              # 하늘 띠 높이 대비 비율(세로 위치)
            "speed": _r.uniform(6.0, 16.0),            # px/초 (오른쪽으로 흐름, 월드 기준)
            "scale": _r.uniform(0.7, 1.15),            # 크기 변주
            "base": _r.choice(self._cloud_imgs),       # 이 구름이 쓸 원본 그림
            "img": None,                               # 크기 적용된 그림(필요할 때 생성·캐시)
        }

    @staticmethod
    def _make_cloud_surface():
        """(폴백) 반투명 흰 뭉게구름 한 덩이를 미리 그려 둔다(여러 원을 겹쳐 puffy 하게)."""
        w, h = 180, 80
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        col = (255, 255, 255, 150)
        for cx, cy, r in [(60, 50, 30), (95, 40, 36), (130, 50, 26),
                          (80, 54, 26), (115, 56, 22)]:
            pygame.draw.circle(surf, col, (cx, cy), r)
        return surf

    def update_sky(self, dt):
        """구름을 흐르게 하고, 날씨에 맞춰 구름 수를 서서히 맞춘다(흐림·비엔 더 많게)."""
        # [←호출] run() 루프 매 프레임.
        import random as _r
        margin = 220
        # 날씨별 목표 구름 수로 조금씩 수렴(한 프레임에 ±1)
        target = self.CLOUD_COUNTS.get(self.world.environment.weather, 5)
        if len(self.clouds) < target:
            self.clouds.append(self._new_cloud(x=-margin))   # 왼쪽에서 흘러 들어옴
        elif len(self.clouds) > target:
            self.clouds.pop()
        for c in self.clouds:
            c["x"] += c["speed"] * dt            # 오른쪽으로 흐름
            if c["x"] > self.world.width + margin:   # 맵 오른쪽 끝을 지나면 왼쪽에서 다시
                c["x"] = -margin
                c["yf"] = _r.uniform(0.08, 0.55)
                c["base"] = _r.choice(self._cloud_imgs)
                c["img"] = None

    def draw_sky(self, procedural=False):
        """하늘에 해/달과 구름을 띄운다. 지평선(field_top) 위 영역에만 그린다.
        배경 그림이 없을 때(procedural=True)만 절차적 하늘(그라데이션+언덕)도 깐다."""
        band_h = self.field_top                 # 하늘 영역 높이
        if procedural:
            # 배경 그림이 없으면 위→아래 그라데이션으로 하늘을 직접 칠한다.
            top_col, bot_col = self._sky_colors()
            band = pygame.Surface((self.screen_width, band_h))
            for i in range(band_h):
                f = i / max(1, band_h - 1)      # 0(위)~1(아래)
                col = (int(top_col[0] + (bot_col[0] - top_col[0]) * f),
                       int(top_col[1] + (bot_col[1] - top_col[1]) * f),
                       int(top_col[2] + (bot_col[2] - top_col[2]) * f))
                pygame.draw.line(band, col, (0, i), (self.screen_width, i))
            self.screen.blit(band, (0, 0))
        # 해/달·구름은 하늘 영역(지평선 위)에만 보이도록 클립
        # [문법] set_clip : 이후 그리기를 이 사각형 안으로만 제한(밖은 안 그려짐).
        prev_clip = self.screen.get_clip()
        self.screen.set_clip(pygame.Rect(0, 0, self.screen_width, band_h))
        self._draw_sun_or_moon(band_h)
        cam_x = self.camera.x * self.CLOUD_PARALLAX   # 패럴랙스: 카메라보다 천천히 움직여 멀리 있는 느낌
        for c in self.clouds:
            base = c["base"]
            need = (max(1, int(base.get_width() * c["scale"])),
                    max(1, int(base.get_height() * c["scale"])))
            if c["img"] is None or c["img"].get_size() != need:
                c["img"] = pygame.transform.smoothscale(base, need)   # 크기 적용(캐시)
            img = c["img"]
            screen_x = int(c["x"] - cam_x)
            # 화면 좌우로 약간 벗어난 사본도 그려, 화면 경계를 넘나들 때 끊겨 보이지 않게 한다.
            for sx in (screen_x, screen_x - self.world.width, screen_x + self.world.width):
                if -img.get_width() <= sx <= self.screen_width:
                    self.screen.blit(img, (sx, int(c["yf"] * band_h - img.get_height() / 2)))
        self.screen.set_clip(prev_clip)         # 클립 원상 복구
        if procedural:   # 그림이 없을 때만 절차적 지평선(언덕)도 그린다
            self._draw_horizon(band_h, self._sky_colors()[1])

    def _draw_horizon(self, band_h, sky_bot):
        """지평선을 인디게임처럼 부드럽게: 옅은 안개(원근감) + 굽이치는 먼 언덕 3겹.
        가장 앞 언덕은 초원과 같은 색이라 아래 초원으로 자연스럽게 이어진다."""
        import math
        w = self.screen_width
        grass = BACKGROUND_COLOR

        def blend(a, b, t):
            """두 색 a,b 를 비율 t 로 섞는다(중첩 함수)."""
            return tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))

        # 1) 안개: 띠 하단 ~46px 를 하늘색→풀색으로 부드럽게(아래로 갈수록 옅게)
        haze_h = 46
        haze = pygame.Surface((w, haze_h), pygame.SRCALPHA)
        for i in range(haze_h):
            f = i / (haze_h - 1)
            c = blend(sky_bot, grass, f)
            # [문법] (*c, ...) : 튜플 c 를 풀어 (R,G,B,A) 로 만든다.
            pygame.draw.line(haze, (*c, int(160 * (1 - f))), (0, i), (w, i))
        self.screen.blit(haze, (0, band_h - haze_h))

        # 2) 굽이치는 언덕 3겹(뒤→앞). 뒤는 하늘에 섞인 옅은 초록, 앞은 초원색.
        layers = [
            (band_h - 30, 13, 0.012, 0.4, blend(sky_bot, grass, 0.6)),
            (band_h - 19, 17, 0.009, 2.1, blend((92, 150, 98), grass, 0.4)),
            (band_h - 7,  21, 0.013, 4.7, grass),
        ]
        for base_y, amp, freq, phase, color in layers:
            pts = [(0, band_h)]
            x = 0
            while x <= w:
                # 사인파로 물결치는 언덕 윤곽선 점들을 만든다.
                pts.append((x, base_y - math.sin(x * freq + phase) * amp))
                x += 8
            pts.append((w, band_h))
            pygame.draw.polygon(self.screen, color, pts)

    def _sky_colors(self):
        """게임 시간에 따라 (하늘 위쪽색, 아래쪽색) 을 돌려준다. 낮/노을/밤 보간."""
        t = self.world.environment.time
        # 키프레임: 시각 → (위, 아래)
        keys = [
            (0.0,  (12, 16, 40),  (30, 34, 64)),    # 한밤
            (5.0,  (12, 16, 40),  (30, 34, 64)),
            (7.0,  (240, 150, 90), (255, 210, 150)),  # 일출(노을)
            (9.0,  (84, 150, 222), (170, 210, 240)),  # 아침
            (16.0, (84, 150, 222), (170, 210, 240)),  # 낮
            (18.5, (240, 140, 80), (255, 195, 130)),  # 일몰(노을)
            (20.0, (12, 16, 40),  (30, 34, 64)),    # 밤
            (24.0, (12, 16, 40),  (30, 34, 64)),
        ]
        # [문법] zip(keys, keys[1:]) : 이웃한 두 키프레임을 짝지어, 현재 시각이 든 구간을 찾는다.
        for (t0, top0, bot0), (t1, top1, bot1) in zip(keys, keys[1:]):
            if t0 <= t <= t1:
                f = (t - t0) / (t1 - t0) if t1 > t0 else 0.0   # 구간 내 진행률
                lerp = lambda a, b: tuple(int(a[k] + (b[k] - a[k]) * f) for k in range(3))
                return lerp(top0, top1), lerp(bot0, bot1)      # 두 키프레임 색을 보간
        return (84, 150, 222), (170, 210, 240)

    def _draw_sun_or_moon(self, band_h):
        """게임 시간(0~24h)에 따라 해(낮)·달(밤)이 하늘 띠를 가로질러 떠간다.
        sun.png/moon.png 가 있으면 그 그림을, 없으면 절차적 원+후광을 그린다."""
        import math
        t = self.world.environment.time
        size = 60   # 그림 표시 크기(긴 변, px)
        if 6.0 <= t <= 18.0:                       # 낮 → 해
            frac = (t - 6.0) / 12.0                # 0(아침6시)~1(저녁6시)
            color, glow = (255, 236, 140), (255, 220, 110)
            img = self._sun_img
        else:                                      # 밤 → 달
            frac = ((t - 18.0) / 12.0) if t > 18.0 else ((t + 6.0) / 12.0)
            color, glow = (238, 242, 255), (190, 205, 240)
            img = self._moon_img
        x = int(frac * self.screen_width)          # 가로로 가로질러 이동
        # 띠 안에서 호를 그리며 정오/자정에 가장 높다.
        y = int(band_h * 0.62 - math.sin(frac * math.pi) * band_h * 0.42)
        if img is not None:
            scaled = self._disc(img, size)
            self.screen.blit(scaled, (x - scaled.get_width() // 2, y - scaled.get_height() // 2))
            return
        # 그림이 없으면 후광 원 + 본체 원을 직접 그림
        for i, r in enumerate((44, 36, 28)):
            halo = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(halo, (*glow, 45 + i * 30), (r, r), r)
            self.screen.blit(halo, (x - r, y - r))
        disc = pygame.Surface((44, 44), pygame.SRCALPHA)
        pygame.draw.circle(disc, (*color, 255), (22, 22), 20)
        self.screen.blit(disc, (x - 22, y - 22))

    def _disc(self, img, size):
        """해/달 그림을 size(긴 변, px)에 맞춰 한 번만 키워 캐시한다."""
        cache = getattr(self, "_disc_cache", None)
        if cache is None:
            cache = self._disc_cache = {}
        key = (id(img), size)
        scaled = cache.get(key)
        if scaled is None:
            scaled = cache[key] = scale_longest(img, size)
        return scaled

    # ── 몹 클릭 선택 ─────────────────────────────────────────────────────
    def handle_click(self, screen_pos):
        """화면 좌표를 클릭했을 때:
        - 그 자리에 몹(동물)이 있으면 선택해 우상단에 속성(좌표 포함)을 띄운다.
        - 몹이 없으면 '맵의 그 지점'을 클릭한 것으로 보고 좌표를 기억해
          왼쪽 아래 UI에 표시한다. 같은 몹을 다시 클릭하면 선택 해제."""
        # [←호출] run() 루프에서 '클릭'으로 판정됐을 때.
        wx = screen_pos[0] + self.camera.x        # 화면 → 월드 x
        wy = screen_pos[1] - self.field_top       # 화면 → 월드 y
        click_pos = Vector2(wx, wy)
        best, best_d = None, None                 # 가장 가까운 후보·그 거리
        for a in self.world.living_animals():
            r = max(self.display_size(a) / 2, a.radius)   # 클릭 판정 반경
            # 날고 있는 개체(독수리 등)는 화면상 altitude 만큼 위로 띄워 그려지므로,
            # 클릭 판정도 그 그려진 위치 기준으로 맞춰야 화면에 보이는 자리를 클릭할 수 있다.
            altitude = getattr(a, "altitude", 0.0)
            draw_pos = Vector2(a.position.x, a.position.y - altitude) if altitude else a.position
            d = draw_pos.distance_to(click_pos)
            if d <= r and (best_d is None or d < best_d):
                best, best_d = a, d
        # 동물이 없으면 지형(평지 제외)·자원·식물도 클릭해 속성을 볼 수 있다
        if best is None:
            others = [t for t in self.world.terrains if t.name != "Plain"]
            others += [r for r in self.world.resources if r.alive]
            others += [p for p in self.world.plants if p.alive]
            for e in others:
                r = max(self.display_size(e) / 2, getattr(e, "radius", 10))
                d = e.position.distance_to(click_pos)
                if d <= r and (best_d is None or d < best_d):
                    best, best_d = e, d
        if best is not None:
            # 같은 것을 다시 클릭하면 선택 해제(토글)
            self.selected = None if best is self.selected else best
            self.clicked_point = None        # 몹을 선택했으면 지점 표시는 끔
        else:
            self.selected = None
            self.clicked_point = click_pos    # 빈 곳 클릭 → 그 지점의 월드 좌표 기억

    def _entity_info_lines(self, e):
        """동물이 아닌 개체(지형·자원·식물)의 속성 줄 목록 — 가진 속성만 골라 보여준다."""
        lines = [f"{e.name}  (#{e.id})",
                 f"좌표: ({e.position.x:.0f}, {e.position.y:.0f})",
                 f"종류: {e.kind}"]
        # [문법] hasattr 로 '그 속성이 있을 때만' 줄을 추가(개체마다 가진 속성이 달라서).
        if hasattr(e, "max_health"):
            lines.append(f"체력: {e.health:.0f} / {e.max_health:.0f}")
        if hasattr(e, "amount"):
            lines.append(f"남은 양: {e.amount:.0f} / {e.max_amount:.0f}")
        if hasattr(e, "water"):
            lines.append(f"물의 양: {e.water:.0f} / {e.max_water:.0f}")
        if hasattr(e, "leaf_amount"):
            lines.append(f"잎의 양: {e.leaf_amount:.0f} / {e.max_leaf:.0f}")
        if hasattr(e, "current_foliage"):
            lines.append(f"덤불 잎: {e.current_foliage:.0f} / {e.max_foliage:.0f}")
        if getattr(e, "action_text", ""):
            lines.append(f"상태: {e.action_text}")
        return lines

    def draw_selection_panel(self):
        """선택된 개체(동물/지형/자원/식물)의 속성을 우상단 패널에 보여준다."""
        a = self.selected
        if a is None or not getattr(a, "alive", False):
            self.selected = None             # 선택한 게 죽었으면 해제
            return
        if getattr(a, "kind", "") == "animal":
            # 동물은 풍부한 스탯을 보여준다.
            lines = [
                f"{a.name}  (#{a.id})",
                f"좌표: ({a.position.x:.0f}, {a.position.y:.0f})",
                f"종류: {getattr(a, 'diet_type', '') or a.kind}",
                f"체력: {a.health:.0f} / {a.max_health:.0f}",
                f"허기: {a.hunger:.0f}   갈증: {a.thirst:.0f}",
                f"기력: {a.stamina:.0f}   스트레스: {a.stress:.0f}",
                f"나이: {a.age:.1f}   속도: {a.speed:.1f}   공격력: {a.power:.1f}",
                f"행동: {a.action_text or '-'}",
            ]
        else:
            lines = self._entity_info_lines(a)
        pw, ph = 250, 24 + 22 * len(lines)       # 패널 크기(줄 수에 맞춤)
        panel = pygame.Rect(self.screen_width - pw - 16, 16, pw, ph)   # 우상단 위치
        pygame.draw.rect(self.screen, PANEL_COLOR, panel, border_radius=8)
        pygame.draw.rect(self.screen, PANEL_BORDER, panel, 2, border_radius=8)
        for i, line in enumerate(lines):
            font = self.font if i == 0 else self.small_font   # 첫 줄(이름)만 큰 글꼴
            self.screen.blit(font.render(line, True, TEXT_COLOR),
                             (panel.x + 14, panel.y + 12 + i * 22))

    def draw_rain(self):
        """비가 올 때 화면 전체에 비스듬히 떨어지는 빗줄기를 그린다(가벼운 입자 애니메이션)."""
        if self.world.environment.weather != "rain":
            return
        import random as _r
        dt = getattr(self, "dt", 0.0)
        w, h = self.screen_width, self.screen_height
        for d in self.raindrops:                 # d = [x, y, 낙하속도]
            d[1] += d[2] * dt                    # 아래로
            d[0] -= d[2] * 0.22 * dt              # 약간 왼쪽으로 비스듬히
            if d[1] > h:                          # 바닥에 닿으면 위에서 다시(x 재배치)
                d[0], d[1] = _r.uniform(0, w), _r.uniform(-20, 0)
            x, y = int(d[0]), int(d[1])
            pygame.draw.line(self.screen, (175, 195, 225), (x, y), (x - 5, y + 12), 1)

    # [변수] _WEATHER_TOOLTIP : 날씨 아이콘에 마우스를 올렸을 때 보여줄 효과 설명 줄들.
    _WEATHER_TOOLTIP = {
        "sunny":   ["☀ 맑음", "갈증 소모 약간 증가", "식물 성장 정상 (×1.0)", "전투력 정상"],
        "cloudy":  ["☁ 흐림", "체력 +0.5/s 회복", "식물 성장 증가 (×1.15)", "전투력 정상"],
        "rain":    ["🌧 비", "체력 +0.5/s 회복", "식물 성장 촉진 (×1.9)",
                   "호수·웅덩이 보충", "전투력 소폭 상승 (×1.05)"],
        "drought": ["🔥 가뭄", "갈증 빠르게 증가", "스태미나 -2.7/s (그늘 밖)",
                   "체력 -0.6/s (그늘 밖)", "물 고갈 진행", "식물 성장 급감 (×0.35)",
                   "전투력 하락 (×0.85)"],
    }

    def draw_weather_tooltip(self):
        """날씨 아이콘 위에 마우스가 올라오면 효과 요약 툴팁을 띄운다."""
        if self.info_collapsed or self.weather_icon_rect is None:
            return
        mx, my = pygame.mouse.get_pos()
        if not self.weather_icon_rect.collidepoint(mx, my):   # 아이콘 위가 아니면 안 띄움
            return
        weather = self.world.environment.weather
        lines = self._WEATHER_TOOLTIP.get(weather, [weather])
        pad, line_h = 10, 18
        # [문법] max(...size(l)[0] for l in lines) : 가장 긴 줄의 픽셀 너비로 툴팁 폭을 맞춤.
        w = max(self.small_font.size(l)[0] for l in lines) + pad * 2
        h = line_h * len(lines) + pad * 2
        # 아이콘 바로 위에 띄우되 화면 밖으로 나가지 않게 조정
        tx = max(0, min(mx, self.screen_width - w))
        ty = max(0, self.weather_icon_rect.top - h - 6)
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((30, 30, 30, 200))
        pygame.draw.rect(surf, (180, 180, 180, 160), (0, 0, w, h), 1)
        for i, line in enumerate(lines):
            color = (255, 220, 80) if i == 0 else (220, 220, 220)   # 첫 줄(제목)만 노랑
            txt = self.small_font.render(line, True, color)
            surf.blit(txt, (pad, pad + i * line_h))
        self.screen.blit(surf, (tx, ty))

    def draw_weather_tint(self):
        """날씨를 화면 전체에 은은한 반투명 색으로 덧칠(하늘 밴드 대체)."""
        color = WEATHER_TINT.get(self.world.environment.weather)
        if not color:
            return
        tint = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        tint.fill(color)                         # (R,G,B,A) — A 가 투명도
        self.screen.blit(tint, (0, 0))

    def _weather_icon(self, name, size):
        """날씨 아이콘을 size(긴 변, px)에 맞춰 한 번만 키워 캐시한다."""
        cache = getattr(self, "_weather_icon_cache", None)
        if cache is None:
            cache = self._weather_icon_cache = {}
        scaled = cache.get(name)
        if scaled is None:
            img = get_weather_icon(name)
            if img is None:
                cache[name] = False              # 없음을 기억(매번 디스크 안 봄)
                return None
            scaled = cache[name] = scale_longest(img, size)
        return scaled or None                    # False면 None 반환

    def _draw_translucent_panel(self, rect, alpha=200):
        """반투명 패널 배경을 그린다 — UI는 항상 맨 위 레이어로 그려지지만,
        뒤가 비치게 해서 패널 아래 영역(아래쪽 초원)의 동물·식물도 가려지지 않고 보이게 한다."""
        surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(surf, (*PANEL_COLOR, alpha), surf.get_rect(), border_radius=8)
        self.screen.blit(surf, rect.topleft)
        pygame.draw.rect(self.screen, PANEL_BORDER, rect, 2, border_radius=8)

    def _draw_toggle_button(self, rect, expand):
        """정보 패널 접기/펼치기 버튼을 그린다. expand=True 면 '펼치기'(▲), False 면 '접기'(▼)."""
        pygame.draw.rect(self.screen, PANEL_BORDER, rect, border_radius=5)
        cx, cy = rect.center
        w, h = rect.width // 4, rect.height // 5
        if expand:
            pts = [(cx - w, cy + h), (cx + w, cy + h), (cx, cy - h)]   # 위 화살표
        else:
            pts = [(cx - w, cy - h), (cx + w, cy - h), (cx, cy + h)]   # 아래 화살표
        pygame.draw.polygon(self.screen, PANEL_COLOR, pts)

    def draw_ui(self):
        """좌하단 정보 패널(Day·시각·온도·배속·날씨·동물 수·미니맵)을 그린다."""
        # [←호출] draw().
        # 정보 패널을 '좌하단'에 둔다(상단은 하늘 띠가 차지하므로).
        # 접힌 상태면 작은 막대만, 펼친 상태면 전체 정보를 보여준다. 우상단 모서리의
        # 작은 버튼(▲/▼)으로 접고 펼 수 있다.
        env = self.world.environment
        btn_size = 22
        if self.info_collapsed:                  # ── 접힌 상태: 작은 막대만 ──
            ph = btn_size + 12
            panel = pygame.Rect(16, self.screen_height - ph - 14,
                                220, ph)
            self._draw_translucent_panel(panel)
            label = self.small_font.render(f"Day {env.day}  {env.clock_text()}", True, TEXT_COLOR)
            self.screen.blit(label, (panel.x + 12, panel.y + (ph - label.get_height()) // 2))
            self.info_toggle_rect = pygame.Rect(panel.right - btn_size - 6,
                                                 panel.y + (ph - btn_size) // 2,
                                                 btn_size, btn_size)
            self._draw_toggle_button(self.info_toggle_rect, expand=True)
            if env.ended:
                self.endpanel(env.end_reason)    # (주의) 메서드명 오타: 실제 정의는 end_panel
            return

        # ── 펼친 상태: 전체 정보 ──
        # 타이틀·아이콘을 먼저 측정해 패널 너비를 딱 맞게 계산
        state = "PAUSED" if self.paused else f"x{self.time_scale:g}"
        title = f"Day {env.day} · {env.clock_text()} · {env.temperature}°C · {state}"
        title_surf = self.title_font.render(title, True, TEXT_COLOR)
        icon_size = 26
        icon = self._weather_icon(env.weather, icon_size)
        icon_w = (icon.get_width() if icon is not None else
                  self.title_font.size(env.weather)[0]) + 10
        # 패널 너비 = 왼쪽 여백 + 타이틀 + 간격 + 아이콘 + 토글버튼 + 오른쪽 여백
        row_needed = 16 + title_surf.get_width() + 10 + icon_w + btn_size + 18
        ph = 182
        panel = pygame.Rect(16, self.screen_height - ph - 14,
                            min(max(row_needed, 260), self.screen_width - 32), ph)
        self._draw_translucent_panel(panel)
        self.info_toggle_rect = pygame.Rect(panel.right - btn_size - 8, panel.y + 8,
                                             btn_size, btn_size)
        self._draw_toggle_button(self.info_toggle_rect, expand=False)
        tx, ty = panel.x + 16, panel.y + 12
        self.screen.blit(title_surf, (tx, ty))
        tx += title_surf.get_width() + 10
        # 날씨: 아이콘이 있으면 그림으로, 없으면 영문 텍스트로 표시
        if icon is not None:
            icon_y = ty + (title_surf.get_height() - icon.get_height()) // 2
            self.screen.blit(icon, (tx, icon_y))
            self.weather_icon_rect = pygame.Rect(tx, icon_y, icon.get_width(), icon.get_height())
        else:
            fallback = self.title_font.render(env.weather, True, TEXT_COLOR)
            self.screen.blit(fallback, (tx, ty))
            self.weather_icon_rect = pygame.Rect(tx, ty, fallback.get_width(), fallback.get_height())
        # 타이틀과 동물 수 사이 구분선
        sep_y = panel.y + 42
        pygame.draw.line(self.screen, PANEL_BORDER,
                         (panel.x + 14, sep_y), (panel.right - 14, sep_y), 1)
        # 동물 수: 두 줄로 나눠서 패널 밖으로 삐져나가지 않게
        items = sorted(self.world.counts_by_name().items())
        mid = (len(items) + 1) // 2
        # [문법] "  ".join(f"..." for ...) : 각 종 'name 수' 문자열들을 공백 두 칸으로 이어 붙임.
        row1 = "  ".join(f"{n} {c}" for n, c in items[:mid])
        row2 = "  ".join(f"{n} {c}" for n, c in items[mid:])
        self.screen.blit(self.small_font.render(row1, True, TEXT_COLOR),
                         (panel.x + 16, panel.y + 50))
        if row2:
            self.screen.blit(self.small_font.render(row2, True, TEXT_COLOR),
                             (panel.x + 16, panel.y + 68))
        dim = (58, 72, 48)
        cam = f"드래그 ({int(self.camera.x)}, {int(self.camera.y)})"
        if self.clicked_point is not None:
            cam += f" | 클릭 ({self.clicked_point.x:.0f}, {self.clicked_point.y:.0f})"
        self.screen.blit(self.small_font.render(cam, True, dim),
                         (panel.x + 16, panel.y + 95))
        self.draw_minimap(panel)                 # [호출→] 미니맵
        if env.ended:
            self.end_panel(env.end_reason)        # [호출→] 종료 화면

    def draw_minimap(self, panel):
        """패널 하단에 전체 월드를 축소한 가로 띠 미니맵을 그린다.
        동물은 색깔 점으로 표시하고, 현재 화면 영역은 흰 테두리로 표시한다."""
        mg = 12  # 패널 가장자리 여백
        mm_w = panel.width - mg * 2
        scale = mm_w / max(1, self.world.width)   # 월드 → 미니맵 축소 비율
        mm_h = max(28, int(self.world.height * scale))
        mm_x = panel.x + mg
        mm_y = panel.bottom - mm_h - mg

        # 구분선
        sep_y = mm_y - 8
        pygame.draw.line(self.screen, PANEL_BORDER,
                         (panel.x + 14, sep_y), (panel.right - 14, sep_y), 1)

        # 배경 (초원색)
        pygame.draw.rect(self.screen, (100, 150, 72), (mm_x, mm_y, mm_w, mm_h))

        # 동물 점 (미니맵 영역 밖으로 안 나가게 클립)
        prev_clip = self.screen.get_clip()
        self.screen.set_clip(pygame.Rect(mm_x, mm_y, mm_w, mm_h))
        for animal in self.world.animals:
            if not animal.alive:
                continue
            ax = mm_x + int(animal.position.x * scale)
            ay = mm_y + int(animal.position.y * scale)
            pygame.draw.circle(self.screen, animal.color, (ax, ay), 2)   # 종 색으로 점
        self.screen.set_clip(prev_clip)

        # 현재 화면 영역 표시(흰 테두리 사각형)
        vp_x = mm_x + int(self.camera.x * scale)
        vp_w = max(4, int(self.screen_width * scale))
        pygame.draw.rect(self.screen, (255, 255, 200),
                         (vp_x, mm_y, vp_w, mm_h), 2)

        # 테두리
        pygame.draw.rect(self.screen, PANEL_BORDER, (mm_x, mm_y, mm_w, mm_h), 1)

    def end_panel(self, reason):
        """시뮬레이션 종료(미어캣 엔딩) 시 화면 중앙에 결과·재시작 안내를 띄운다."""
        # [←호출] draw_ui() 에서 env.ended 일 때.
        panel = pygame.Rect(0, 0, min(680, self.screen_width - 48), 150)
        panel.center = (self.screen_width // 2, self.screen_height // 2)
        pygame.draw.rect(self.screen, (245, 235, 211), panel, border_radius=8)
        pygame.draw.rect(self.screen, (92, 65, 50), panel, 3, border_radius=8)
        self.caption("Simulation Ended", panel.centerx, panel.centery - 42,
                   self.title_font, (62, 45, 38))
        self.caption(reason, panel.centerx, panel.centery - 5, self.font, (62, 45, 38))
        self.caption("다시 시작하겠습니까?  [Y] 예   [N] 아니오",
                   panel.centerx, panel.centery + 38, self.font, (92, 65, 50))

    def caption(self, text, x, y, font, color=TEXT_COLOR):
        """(x,y)를 '중심'으로 한 줄 텍스트를 그린다(가운데 정렬 헬퍼)."""
        surface = font.render(text, True, color)
        self.screen.blit(surface, surface.get_rect(center=(x, y)))
