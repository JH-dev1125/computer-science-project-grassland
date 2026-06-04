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
GAME_HOURS_PER_SECOND = 0.25   # 실제 1초 = 게임 0.25h → 하루(24h)=96초
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
