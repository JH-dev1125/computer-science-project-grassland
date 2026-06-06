# =============================================================================
# config.py — 시뮬레이션 전역 상수 (역할: 숫자만 보관, 로직 없음)
# 실험하며 바꿀 모든 수치를 여기 한 곳에 둔다. 다른 파일은 읽기만 한다.
# =============================================================================

# ── 창(화면) ─────────────────────────────────────────────
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
MIN_SCREEN_WIDTH = 900
MIN_SCREEN_HEIGHT = 600

# ── 월드(맵) ─────────────────────────────────────────────
WORLD_WIDTH = 2400
WORLD_HEIGHT = 1600

# ── 시간 ────────────────────────────────────────────────
FPS = 60
GAME_HOURS_PER_SECOND = 1   # 실제 1초 = 게임 0.25h → 하루(24h)=96초
DAY_LENGTH_HOURS = 24

# ── 초기 동물 수 (seed) ──────────────────────────────────
SEED_COUNTS = {
    "Lion": 2, "Hyena": 3, "Bald_Eagle": 2,
    "Zebra": 6, "Gazelle": 6, "Elephant": 2,
    "Meerkat": 5, "Warthog": 4,
}

# ── 색상 (R,G,B) ────────────────────────────────────────
BACKGROUND_COLOR = (126, 184, 92)
GRID_COLOR = (118, 174, 86)
TEXT_COLOR = (34, 42, 28)
PANEL_COLOR = (246, 241, 222)
PANEL_BORDER = (82, 91, 66)

# ── 날씨 틴트 (R,G,B,A) : 화면 전체에 은은히 덧칠 ───────────
WEATHER_TINT = {
    "sunny":   (255, 236, 150, 26),
    "cloudy":  (150, 160, 170, 46),
    "rain":    (70,  100, 140, 70),
    "drought": (232, 150, 60,  74),
}

ASSET_SPRITE_SHEET = "assets/sprites/environment_resource_terrain_sheet.png"

# ── 개체별 이미지(스프라이트) 폴더 ───────────────────────────────
# 각 동물·식물·자원·지형의 PNG 를 여기에 두면 gui 가 자동으로 불러 그린다.
# 파일 이름 규칙: 개체 name 을 소문자로 (예: Lion→lion.png, Bald_Eagle→bald_eagle.png)
# 이미지가 없으면 기존처럼 도형으로 그린다(폴백).
MOB_SPRITE_DIR = "assets/sprites/mobs"

# 표시 배율: 충돌 반지름(radius) 대비 스프라이트를 얼마나 크게 그릴지(종류별).
# florr.io mob 처럼 약간 큼직하게 보이도록 1보다 크게 둔다.
SPRITE_VISUAL_SCALE = {
    "animal": 2.4,
    "plant": 2.2,
    "resource": 2.3,
    "terrain": 2.0,
}
