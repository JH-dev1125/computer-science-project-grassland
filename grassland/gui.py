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
import math
import pygame

from grassland.config import (
    BACKGROUND_COLOR, FPS, GRID_COLOR, MIN_SCREEN_HEIGHT, MIN_SCREEN_WIDTH,
    PANEL_BORDER, PANEL_COLOR, SCREEN_HEIGHT, SCREEN_WIDTH, SKY_BAND_HEIGHT,
    SPRITE_DISPLAY_DEFAULT, SPRITE_DISPLAY_SIZE, TEXT_COLOR, WEATHER_TINT,
)
from grassland.sprites import get_sprite, get_background, get_sky_image, get_weather_icon
from pygame.math import Vector2


class GrasslandApp:
    def __init__(self, world):
        pygame.init()
        pygame.display.set_caption("와글와글 초원 생태계")
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.world = world
        # 세로는 고정(항상 0), 가로만 스크롤. 초원은 하늘 띠(field_top) 아래부터 그린다.
        self.camera = Vector2(220, 0)
        self.field_top = SKY_BAND_HEIGHT
        self.dragging = False
        self._press_pos = None       # 클릭 vs 드래그 구분용(눌렀을 때 화면 좌표)
        self.selected = None         # 클릭으로 선택된 몹(없으면 None)
        self.font = self._font(17)
        self.small_font = self._font(13)
        self.title_font = self._font(22)
        self._init_sky()

    def _font(self, size):
        for name in ("malgungothic", "맑은 고딕", "arial"):
            font = pygame.font.SysFont(name, size)
            if font is not None:
                return font
        return pygame.font.Font(None, size)

    # ── 메인 루프 ────────────────────────────────────────────────────────
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            self.dt = dt
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and self.world.environment.ended:
                    if event.key in (pygame.K_y, pygame.K_RETURN):
                        self._restart()
                    elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                        running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.resize(event.w, event.h)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.dragging = True
                    self._press_pos = event.pos
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.dragging = False
                    # 누른 자리와 뗀 자리가 거의 같으면 '드래그'가 아니라 '클릭' →
                    # 그 위치의 몹을 선택해 속성 패널에 띄운다.
                    if self._press_pos is not None:
                        dx = event.pos[0] - self._press_pos[0]
                        dy = event.pos[1] - self._press_pos[1]
                        if dx * dx + dy * dy <= 25:
                            self.handle_click(event.pos)
                    self._press_pos = None
                elif event.type == pygame.MOUSEMOTION and self.dragging:
                    self.camera.x -= event.rel[0]   # 가로만 이동(세로 고정)
                    self.clamp_camera()
            if not self.world.environment.ended:
                self.world.update(dt)
            self.update_sky(dt)
            self.draw()
        pygame.quit()

    def _restart(self):
        from grassland.world import World
        self.world = World.seed_default()
        self.camera = Vector2(220, 0)
        self.selected = None
        self._init_sky()

    # ── 카메라 ───────────────────────────────────────────────────────────
    def clamp_camera(self):
        self.camera.x = max(0, min(self.camera.x, max(0, self.world.width - self.screen_width)))
        self.camera.y = 0   # 세로 고정

    def resize(self, width, height):
        self.screen_width = max(MIN_SCREEN_WIDTH, width)
        self.screen_height = max(MIN_SCREEN_HEIGHT, height)
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.clamp_camera()

    def world_to_screen(self, position):
        # 세로는 고정 → 월드 y 에 field_top 만 더한다(하늘 띠 아래부터 시작).
        return int(position.x - self.camera.x), int(position.y + self.field_top)

    def visible(self, entity, margin=120):
        x, y = self.world_to_screen(entity.position)
        return -margin <= x <= self.screen_width + margin and \
               -margin <= y <= self.screen_height + margin

    # ── 스프라이트(이미지) 그리기 ────────────────────────────────────────
    def display_size(self, entity):
        """이 개체를 화면에 얼마나 크게(긴 변, px) 그릴지 — config 의 현실적 크기비 표에서."""
        base = SPRITE_DISPLAY_SIZE.get(entity.name, SPRITE_DISPLAY_DEFAULT)
        return int(base * entity.draw_scale)

    def blit_sprite(self, entity, x, y, flip=False, anchor="center"):
        """entity 의 PNG 를 그린다. anchor="bottom" 이면 '발밑'을 (x,y)에 맞춰 위로 세워
        그린다(오블리크 2.5D — 물체가 바닥을 딛고 서 있는 느낌). "center" 면 바닥에
        누운 것(호숫가·웅덩이). 그린 사각형(Rect)을 돌려준다(체력바 위치 계산용)."""
        size = self.display_size(entity)
        sprite = get_sprite(entity.name.lower(), size)
        if sprite is None:
            r = max(4, size // 5)
            pygame.draw.circle(self.screen, (210, 60, 210), (x, y), r)
            return pygame.Rect(x - r, y - r, 2 * r, 2 * r)
        if flip:
            sprite = pygame.transform.flip(sprite, True, False)
        if getattr(entity, "is_hidden", False):   # 숨으면 반투명하게
            if not flip:
                sprite = sprite.copy()
            sprite.set_alpha(130)
        if anchor == "bottom":
            rect = sprite.get_rect(midbottom=(x, y))
        else:
            rect = sprite.get_rect(center=(x, y))
        self.screen.blit(sprite, rect)
        return rect

    def draw_shadow(self, entity, x, y, altitude):
        """떠오른 동물의 발밑(원래 바닥 위치)에 옅은 타원 그림자를 그려 '뜬' 느낌을 강조한다.
        높이 뜰수록 그림자는 작아지고 옅어진다(독수리가 하늘로 멀어지는 인상)."""
        w = max(16, self.display_size(entity) // 2)
        h = max(5, w // 3)
        fade = max(15, 90 - int(altitude * 1.4))
        shadow = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (20, 20, 20, fade), shadow.get_rect())
        self.screen.blit(shadow, shadow.get_rect(center=(x, y)))

    # 바닥에 '누운' 것들(평면). 나머지는 '서 있는' 것으로 보고 발밑을 바닥에 딛는다.
    FLAT_NAMES = ("Lake_Side", "Water_Puddle", "Carcass")

    # ── 그리기(배경그림 → 하늘(해·달·구름) → 깊이정렬된 세계 → UI) ─────────
    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)        # 그림 없을 때 단색 초록
        has_bg = self.draw_background()           # 하늘+땅이 그려진 배경 그림(있으면)
        # 하늘(해·달·구름). 배경 그림이 없으면 절차적 하늘(그라데이션+언덕)도 그린다.
        self.draw_sky(procedural=not has_bg)
        # 세계: 동물·구조물을 발밑 기준·깊이순으로. 동물은 top_margin 으로 하늘에 못 감.
        self.draw_world()
        self.draw_weather_tint()                  # 날씨 틴트
        self.draw_ui()                            # 정보 패널(좌하단)
        self.draw_selection_panel()                # 선택한 몹의 속성 패널(우상단)
        pygame.display.flip()

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
            img = tile if (idx % 2 == 0) else tile_flipped
            self.screen.blit(img, (idx * tile_w - cam_x, 0))
            idx += 1
        return True

    def _scaled_background(self, bg):
        """원본 이미지를 화면 높이에 맞춰 비율 그대로 축소하고(확대와 달리 픽셀이
        깨지지 않음), 거울 타일링용으로 좌우 반전 사본도 함께 만들어 캐시한다."""
        key = int(self.screen_height)
        if getattr(self, "_bg_key", None) != key:
            bw, bh = bg.get_size()
            scale = key / bh
            new_size = (max(1, round(bw * scale)), key)
            self._bg_scaled = pygame.transform.smoothscale(bg, new_size)
            self._bg_flipped = pygame.transform.flip(self._bg_scaled, True, False)
            self._bg_key = key
        return self._bg_scaled, self._bg_flipped

    def draw_world(self):
        # 1) 바닥에 누운 것(호숫가·물웅덩이·사체)을 먼저, 뒤(작은 y)→앞(큰 y) 순으로.
        flat = []
        for t in self.world.terrains:
            if t.name == "Lake_Side" and self.visible(t, 200):
                flat.append(t)
        for r in self.world.resources:
            if r.alive and r.name in ("Water_Puddle", "Carcass") and self.visible(r):
                flat.append(r)
        flat.sort(key=lambda e: e.position.y)
        for e in flat:
            x, y = self.world_to_screen(e.position)
            self.blit_sprite(e, x, y, anchor="center")

        # 2) 서 있는 것(동굴·식물·동물)을 '발밑 y' 기준으로 정렬 — 앞의 것이 뒤를 가린다.
        upright = []
        for t in self.world.terrains:
            if t.name == "Cave" and self.visible(t, 200):
                upright.append(t)
        upright.extend(p for p in self.world.alive_plants() if self.visible(p))
        upright.extend(a for a in self.world.animals if a.alive and self.visible(a))
        upright.sort(key=lambda e: e.position.y)
        for e in upright:
            x, y = self.world_to_screen(e.position)
            if e.kind == "animal":
                dt = getattr(self, 'dt', 0.0)
                if not hasattr(e, '_flip_cooldown'):
                    e._flip_cooldown = 0.0
                e._flip_cooldown = max(0.0, e._flip_cooldown - dt)
                dvx = e.desired_velocity.x
                if e._flip_cooldown <= 0.0:
                    if dvx > 8:
                        e.facing_left = False
                        e._flip_cooldown = 0.4
                    elif dvx < -8:
                        e.facing_left = True
                        e._flip_cooldown = 0.4
                altitude = getattr(e, "altitude", 0.0)
                bt = getattr(e, '_bounce_timer', 0.0)
                bd = getattr(e, '_bounce_duration', 1.0)
                bh = getattr(e, '_bounce_height', 0.0)
                bounce_y = int(math.sin((1.0 - bt / bd) * math.pi) * bh) if bt > 0.0 else 0
                total_lift = int(altitude) + bounce_y
                if altitude > 0.5:
                    self.draw_shadow(e, x, y, altitude)
                rect = self.blit_sprite(e, x, y - total_lift, flip=not getattr(e, "facing_left", True),
                                        anchor="bottom")
                self.health_bar(e, x, rect.top - 6, self.display_size(e))
                if e is self.selected:   # 선택된 몹은 발밑에 고리를 그려 표시
                    rw = max(rect.width, 30)
                    ring = pygame.Rect(0, 0, rw + 14, (rw + 14) // 3)
                    ring.center = (x, y)
                    pygame.draw.ellipse(self.screen, (255, 230, 90), ring, 3)
            else:
                self.blit_sprite(e, x, y, anchor="bottom")

        # 3) 상호작용 선: 행동 중인 동물과 대상 사이를 연결
        self._draw_interaction_lines()

    _INTERACTION_COLORS = {
        "attack": (220, 50,  50),
        "hunt":   (220, 50,  50),
        "fight":  (220, 50,  50),
        "kick":   (220, 50,  50),
        "stomp":  (220, 50,  50),
        "yacha":  (220, 50,  50),
        "steal":  (220, 130, 50),
        "eat":         (80, 200, 80),
        "eat_carcass": (80, 200, 80),
        "graze":       (80, 200, 80),
        "drink": (80, 160, 220),
        "water": (80, 160, 220),
        "flee":    (240, 180, 50),
        "zigzag":  (240, 180, 50),
        "burrow":  (240, 180, 50),
        "carcass": (180, 140, 220),
    }

    def _draw_interaction_lines(self):
        for animal in self.world.animals:
            if not animal.alive:
                continue
            target = getattr(animal, "interaction_target", None)
            if target is None:
                continue
            if not getattr(target, "alive", True):
                continue
            ax, ay = self.world_to_screen(animal.position)
            tx, ty = self.world_to_screen(target.position)
            color = self._INTERACTION_COLORS.get(
                getattr(animal, "action_text", ""), (200, 200, 200))
            pygame.draw.line(self.screen, color, (ax, ay), (tx, ty), 2)

    def health_bar(self, animal, x, y, width):
        """동물 머리 위 체력바. 비율(0~1)에 따라 길이와 색이 바뀐다(초록→노랑→빨강)."""
        mx = animal.max_health if animal.max_health > 0 else 1.0
        ratio = max(0.0, min(1.0, animal.health / mx))
        w = max(26, min(int(width), 96))      # 종별 크기 반영하되 상·하한
        h = 6
        left, top = x - w // 2, y
        pygame.draw.rect(self.screen, (30, 30, 30), (left - 1, top - 1, w + 2, h + 2),
                         border_radius=2)                       # 테두리
        pygame.draw.rect(self.screen, (92, 74, 66), (left, top, w, h), border_radius=2)  # 빈 칸
        if ratio > 0.5:
            col = (96, 200, 96)
        elif ratio > 0.25:
            col = (232, 200, 72)
        else:
            col = (222, 84, 72)
        fw = int(w * ratio)
        if fw > 0:
            pygame.draw.rect(self.screen, col, (left, top, fw, h), border_radius=2)

    # ── 하늘 띠(상단 고정) — 초원과 독립적으로 항상 화면 위쪽에 떠 있다 ───────
    CLOUD_BASE_W = 150        # 구름 한 장의 기준 가로폭(px) — 이미지 원본 크기와 무관하게 통일
    CLOUD_PARALLAX = 0.35     # 카메라 이동에 대한 비율(1=땅과 같이, 0=화면에 고정). 멀리 있는 구름 느낌.

    def _init_sky(self):
        """구름 상태와 그림을 준비. 구름은 '월드' 좌표를 가지고 카메라를 따라(패럴랙스)
        함께 흘러가며, 하늘 띠 안에서 좌우로 떠다닌다.
        cloud1~3.png 가 있으면 그 중 무작위로 골라 쓰고, 없으면 절차적 구름으로 대체."""
        import random as _r
        self._sun_img = get_sky_image("sun")
        self._moon_img = get_sky_image("moon")
        raw_imgs = [im for im in
                    (get_sky_image("cloud1"), get_sky_image("cloud2"), get_sky_image("cloud3"))
                    if im is not None]
        if not raw_imgs:
            raw_imgs = [self._make_cloud_surface()]
        # 원본 이미지 크기가 제각각이라, 가로폭을 기준 크기로 통일해 둔 뒤
        # 개체별로 약간의 변주(scale)만 주어 "너무 크다" 문제를 없앤다.
        self._cloud_imgs = []
        for im in raw_imgs:
            w, h = im.get_size()
            ratio = self.CLOUD_BASE_W / max(1, w)
            new_size = (self.CLOUD_BASE_W, max(1, round(h * ratio)))
            self._cloud_imgs.append(pygame.transform.smoothscale(im, new_size))
        self.clouds = []
        for _ in range(5):
            self.clouds.append({
                "x": _r.uniform(0, self.world.width),      # 월드 px (가로 위치) — 카메라와 함께 흐름
                "yf": _r.uniform(0.08, 0.55),              # 하늘 띠 높이 대비 비율
                "speed": _r.uniform(6.0, 16.0),            # px/초 (오른쪽으로 흐름, 월드 기준)
                "scale": _r.uniform(0.7, 1.15),
                "base": _r.choice(self._cloud_imgs),       # 이 구름이 쓸 원본 그림
                "img": None,
            })

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
        """구름을 흐르게 한다(월드 좌표 기준. 월드 끝을 넘어가면 반대쪽에서, 모양도 새로 골라 등장)."""
        import random as _r
        margin = 220
        for c in self.clouds:
            c["x"] += c["speed"] * dt
            if c["x"] > self.world.width + margin:
                c["x"] = -margin
                c["yf"] = _r.uniform(0.08, 0.55)
                c["base"] = _r.choice(self._cloud_imgs)
                c["img"] = None

    def draw_sky(self, procedural=False):
        """하늘에 해/달과 구름을 띄운다. 지평선(field_top) 위 영역에만 그린다.
        배경 그림이 없을 때(procedural=True)만 절차적 하늘(그라데이션+언덕)도 깐다."""
        band_h = self.field_top
        if procedural:
            top_col, bot_col = self._sky_colors()
            band = pygame.Surface((self.screen_width, band_h))
            for i in range(band_h):
                f = i / max(1, band_h - 1)
                col = (int(top_col[0] + (bot_col[0] - top_col[0]) * f),
                       int(top_col[1] + (bot_col[1] - top_col[1]) * f),
                       int(top_col[2] + (bot_col[2] - top_col[2]) * f))
                pygame.draw.line(band, col, (0, i), (self.screen_width, i))
            self.screen.blit(band, (0, 0))
        # 해/달·구름은 하늘 영역(지평선 위)에만 보이도록 클립
        prev_clip = self.screen.get_clip()
        self.screen.set_clip(pygame.Rect(0, 0, self.screen_width, band_h))
        self._draw_sun_or_moon(band_h)
        cam_x = self.camera.x * self.CLOUD_PARALLAX   # 패럴랙스: 카메라보다 천천히 움직여 멀리 있는 느낌
        for c in self.clouds:
            base = c["base"]
            need = (max(1, int(base.get_width() * c["scale"])),
                    max(1, int(base.get_height() * c["scale"])))
            if c["img"] is None or c["img"].get_size() != need:
                c["img"] = pygame.transform.smoothscale(base, need)
            img = c["img"]
            screen_x = int(c["x"] - cam_x)
            # 화면 좌우로 약간 벗어난 사본도 그려, 화면 경계를 넘나들 때 끊겨 보이지 않게 한다.
            for sx in (screen_x, screen_x - self.world.width, screen_x + self.world.width):
                if -img.get_width() <= sx <= self.screen_width:
                    self.screen.blit(img, (sx, int(c["yf"] * band_h - img.get_height() / 2)))
        self.screen.set_clip(prev_clip)
        if procedural:   # 그림이 없을 때만 절차적 지평선(언덕)도 그린다
            self._draw_horizon(band_h, self._sky_colors()[1])

    def _draw_horizon(self, band_h, sky_bot):
        """지평선을 인디게임처럼 부드럽게: 옅은 안개(원근감) + 굽이치는 먼 언덕 3겹.
        가장 앞 언덕은 초원과 같은 색이라 아래 초원으로 자연스럽게 이어진다."""
        import math
        w = self.screen_width
        grass = BACKGROUND_COLOR

        def blend(a, b, t):
            return tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3))

        # 1) 안개: 띠 하단 ~46px 를 하늘색→풀색으로 부드럽게(아래로 갈수록 옅게)
        haze_h = 46
        haze = pygame.Surface((w, haze_h), pygame.SRCALPHA)
        for i in range(haze_h):
            f = i / (haze_h - 1)
            c = blend(sky_bot, grass, f)
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
        for (t0, top0, bot0), (t1, top1, bot1) in zip(keys, keys[1:]):
            if t0 <= t <= t1:
                f = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
                lerp = lambda a, b: tuple(int(a[k] + (b[k] - a[k]) * f) for k in range(3))
                return lerp(top0, top1), lerp(bot0, bot1)
        return (84, 150, 222), (170, 210, 240)

    def _draw_sun_or_moon(self, band_h):
        """게임 시간(0~24h)에 따라 해(낮)·달(밤)이 하늘 띠를 가로질러 떠간다.
        sun.png/moon.png 가 있으면 그 그림을, 없으면 절차적 원+후광을 그린다."""
        import math
        t = self.world.environment.time
        size = 60   # 그림 표시 크기(긴 변, px)
        if 6.0 <= t <= 18.0:                       # 낮 → 해
            frac = (t - 6.0) / 12.0
            color, glow = (255, 236, 140), (255, 220, 110)
            img = self._sun_img
        else:                                      # 밤 → 달
            frac = ((t - 18.0) / 12.0) if t > 18.0 else ((t + 6.0) / 12.0)
            color, glow = (238, 242, 255), (190, 205, 240)
            img = self._moon_img
        x = int(frac * self.screen_width)
        # 띠 안에서 호를 그리며 정오/자정에 가장 높다.
        y = int(band_h * 0.62 - math.sin(frac * math.pi) * band_h * 0.42)
        if img is not None:
            scaled = self._sky_disc(img, size)
            self.screen.blit(scaled, (x - scaled.get_width() // 2, y - scaled.get_height() // 2))
            return
        for i, r in enumerate((44, 36, 28)):
            halo = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(halo, (*glow, 45 + i * 30), (r, r), r)
            self.screen.blit(halo, (x - r, y - r))
        disc = pygame.Surface((44, 44), pygame.SRCALPHA)
        pygame.draw.circle(disc, (*color, 255), (22, 22), 20)
        self.screen.blit(disc, (x - 22, y - 22))

    def _sky_disc(self, img, size):
        """해/달 그림을 size(긴 변, px)에 맞춰 한 번만 키워 캐시한다."""
        cache = getattr(self, "_sky_disc_cache", None)
        if cache is None:
            cache = self._sky_disc_cache = {}
        key = (id(img), size)
        scaled = cache.get(key)
        if scaled is None:
            w, h = img.get_size()
            scale = size / max(w, h)
            new_size = (max(1, round(w * scale)), max(1, round(h * scale)))
            scaled = pygame.transform.smoothscale(img, new_size)
            cache[key] = scaled
        return scaled

    # ── 몹 클릭 선택 ─────────────────────────────────────────────────────
    def handle_click(self, screen_pos):
        """화면 좌표를 클릭했을 때, 그 자리의 몹(동물)을 찾아 선택한다.
        같은 몹을 다시 클릭하면 선택 해제. 빈 곳을 클릭해도 선택 해제."""
        wx = screen_pos[0] + self.camera.x
        wy = screen_pos[1] - self.field_top
        click_pos = Vector2(wx, wy)
        best, best_d = None, None
        for a in self.world.living_animals():
            r = max(self.display_size(a) / 2, a.radius)
            d = a.position.distance_to(click_pos)
            if d <= r and (best_d is None or d < best_d):
                best, best_d = a, d
        if best is not None and best is self.selected:
            self.selected = None
        else:
            self.selected = best

    def draw_selection_panel(self):
        """선택된 몹의 속성을 우상단 패널에 보여준다."""
        a = self.selected
        if a is None or not getattr(a, "alive", False):
            self.selected = None
            return
        lines = [
            f"{a.name}  (#{a.id})",
            f"종류: {getattr(a, 'diet_type', '') or a.kind}",
            f"체력: {a.health:.0f} / {a.max_health:.0f}",
            f"허기: {a.hunger:.0f}   갈증: {a.thirst:.0f}",
            f"기력: {a.stamina:.0f}   스트레스: {a.stress:.0f}",
            f"나이: {a.age:.1f}   속도: {a.speed:.1f}   공격력: {a.power:.1f}",
            f"행동: {a.action_text or '-'}",
        ]
        pw, ph = 250, 24 + 22 * len(lines)
        panel = pygame.Rect(self.screen_width - pw - 16, 16, pw, ph)
        pygame.draw.rect(self.screen, PANEL_COLOR, panel, border_radius=8)
        pygame.draw.rect(self.screen, PANEL_BORDER, panel, 2, border_radius=8)
        for i, line in enumerate(lines):
            font = self.font if i == 0 else self.small_font
            self.screen.blit(font.render(line, True, TEXT_COLOR),
                             (panel.x + 14, panel.y + 12 + i * 22))

    def draw_weather_tint(self):
        """날씨를 화면 전체에 은은한 반투명 색으로 덧칠(하늘 밴드 대체)."""
        color = WEATHER_TINT.get(self.world.environment.weather)
        if not color:
            return
        tint = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        tint.fill(color)
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
                cache[name] = False
                return None
            w, h = img.get_size()
            scale = size / max(w, h)
            new_size = (max(1, round(w * scale)), max(1, round(h * scale)))
            scaled = pygame.transform.smoothscale(img, new_size)
            cache[name] = scaled
        return scaled or None

    def draw_ui(self):
        # 정보 패널을 '좌하단'에 둔다(상단은 하늘 띠가 차지하므로).
        ph = 92
        panel = pygame.Rect(16, self.screen_height - ph - 14,
                            min(700, self.screen_width - 32), ph)
        pygame.draw.rect(self.screen, PANEL_COLOR, panel, border_radius=8)
        pygame.draw.rect(self.screen, PANEL_BORDER, panel, 2, border_radius=8)
        env = self.world.environment
        title = f"Day {env.day}  {env.clock_text()}   Temp: {env.temperature}C"
        tx, ty = panel.x + 16, panel.y + 12
        title_surf = self.title_font.render(title, True, TEXT_COLOR)
        self.screen.blit(title_surf, (tx, ty))
        tx += title_surf.get_width() + 12
        # 날씨: 아이콘이 있으면 "sunny" 같은 영문 대신 그림으로 표시
        icon_size = 64
        icon = self._weather_icon(env.weather, icon_size)
        if icon is not None:
            # 패널 세로 중앙에 맞춰 배치(아이콘이 글자보다 커서, 패널 전체 높이 기준 중앙정렬).
            icon_y = panel.y + (panel.height - icon.get_height()) // 2
            self.screen.blit(icon, (tx, icon_y))
        else:
            fallback = self.title_font.render(f"Weather: {env.weather}", True, TEXT_COLOR)
            self.screen.blit(fallback, (tx, ty))
        counts = self.world.counts_by_name()
        ctext = " | ".join(f"{n}:{c}" for n, c in sorted(counts.items()))
        self.screen.blit(self.font.render(ctext, True, TEXT_COLOR),
                         (panel.x + 16, panel.y + 44))
        cam = f"Map {int(self.camera.x)},{int(self.camera.y)} / drag to move"
        self.screen.blit(self.small_font.render(cam, True, TEXT_COLOR),
                         (panel.x + 16, panel.y + 69))
        if env.ended:
            self.end_panel(env.end_reason)

    def end_panel(self, reason):
        panel = pygame.Rect(0, 0, min(680, self.screen_width - 48), 150)
        panel.center = (self.screen_width // 2, self.screen_height // 2)
        pygame.draw.rect(self.screen, (245, 235, 211), panel, border_radius=8)
        pygame.draw.rect(self.screen, (92, 65, 50), panel, 3, border_radius=8)
        self.label("Simulation Ended", panel.centerx, panel.centery - 42,
                   self.title_font, (62, 45, 38))
        self.label(reason, panel.centerx, panel.centery - 5, self.font, (62, 45, 38))
        self.label("다시 시작하겠습니까?  [Y] 예   [N] 아니오",
                   panel.centerx, panel.centery + 38, self.font, (92, 65, 50))

    def label(self, text, x, y, font, color=TEXT_COLOR):
        surface = font.render(text, True, color)
        self.screen.blit(surface, surface.get_rect(center=(x, y)))
