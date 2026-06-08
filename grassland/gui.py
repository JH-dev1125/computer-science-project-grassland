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
import pygame

from grassland.config import (
    BACKGROUND_COLOR, FPS, GRID_COLOR, MIN_SCREEN_HEIGHT, MIN_SCREEN_WIDTH,
    PANEL_BORDER, PANEL_COLOR, SCREEN_HEIGHT, SCREEN_WIDTH, SKY_BAND_HEIGHT,
    SPRITE_DISPLAY_DEFAULT, SPRITE_DISPLAY_SIZE, TEXT_COLOR, WEATHER_TINT,
)
from grassland.sprites import get_sprite, get_background
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
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.resize(event.w, event.h)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.dragging = True
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.dragging = False
                elif event.type == pygame.MOUSEMOTION and self.dragging:
                    self.camera.x -= event.rel[0]   # 가로만 이동(세로 고정)
                    self.clamp_camera()
            self.world.update(dt)
            self.update_sky(dt)
            self.draw()
        pygame.quit()

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
        pygame.display.flip()

    def draw_background(self):
        """배경 그림(assets/sprites/background.png)을 화면 가득 깐다.
        월드 가로폭에 맞춰 늘려 카메라와 1:1 로 가로 스크롤(동물이 미끄러지지 않게).
        그림이 없으면 False — 이때는 단색 초록 + 절차적 하늘로 폴백."""
        bg = get_background()
        if bg is None:
            return False
        scaled = self._scaled_background(bg)
        self.screen.blit(scaled, (-int(self.camera.x), 0))
        return True

    def _scaled_background(self, bg):
        """배경 그림을 (월드폭 × 화면높이)로 한 번만 키워 캐시한다."""
        key = (int(self.world.width), int(self.screen_height))
        if getattr(self, "_bg_key", None) != key:
            self._bg_scaled = pygame.transform.smoothscale(bg, key)
            self._bg_key = key
        return self._bg_scaled

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
                if e.velocity.x > 6:
                    e.facing_left = False
                elif e.velocity.x < -6:
                    e.facing_left = True
                rect = self.blit_sprite(e, x, y, flip=not getattr(e, "facing_left", True),
                                        anchor="bottom")
                self.health_bar(e, x, rect.top - 6, self.display_size(e))
            else:
                self.blit_sprite(e, x, y, anchor="bottom")

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
    def _init_sky(self):
        """구름 상태와 그림을 준비. 구름은 화면(시점)에 고정되어 하늘 띠 안에서 흐른다."""
        import random as _r
        self._cloud_img = self._make_cloud_surface()
        self.clouds = []
        for _ in range(5):
            self.clouds.append({
                "x": _r.uniform(-200, SCREEN_WIDTH),       # 화면 px (가로 위치)
                "yf": _r.uniform(0.08, 0.62),              # 하늘 띠 높이 대비 비율
                "speed": _r.uniform(6.0, 16.0),            # px/초 (오른쪽으로 흐름)
                "scale": _r.uniform(0.5, 1.1),
                "img": None,
            })

    @staticmethod
    def _make_cloud_surface():
        """반투명 흰 뭉게구름 한 덩이를 미리 그려 둔다(여러 원을 겹쳐 puffy 하게)."""
        w, h = 180, 80
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        col = (255, 255, 255, 150)
        for cx, cy, r in [(60, 50, 30), (95, 40, 36), (130, 50, 26),
                          (80, 54, 26), (115, 56, 22)]:
            pygame.draw.circle(surf, col, (cx, cy), r)
        return surf

    def update_sky(self, dt):
        """구름을 흐르게 한다(화면 밖으로 나가면 반대쪽에서 다시 등장)."""
        import random as _r
        margin = 220
        for c in self.clouds:
            c["x"] += c["speed"] * dt
            if c["x"] > self.screen_width + margin:
                c["x"] = -margin
                c["yf"] = _r.uniform(0.08, 0.62)

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
        for c in self.clouds:
            need = (int(self._cloud_img.get_width() * c["scale"]),
                    int(self._cloud_img.get_height() * c["scale"]))
            if c["img"] is None or c["img"].get_size() != need:
                c["img"] = pygame.transform.smoothscale(self._cloud_img, need)
            self.screen.blit(c["img"], (int(c["x"]), int(c["yf"] * band_h)))
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
        """게임 시간(0~24h)에 따라 해(낮)·달(밤)이 하늘 띠를 가로질러 떠간다."""
        import math
        t = self.world.environment.time
        if 6.0 <= t <= 18.0:                       # 낮 → 해
            frac = (t - 6.0) / 12.0
            color, glow = (255, 236, 140), (255, 220, 110)
        else:                                      # 밤 → 달
            frac = ((t - 18.0) / 12.0) if t > 18.0 else ((t + 6.0) / 12.0)
            color, glow = (238, 242, 255), (190, 205, 240)
        x = int(frac * self.screen_width)
        # 띠 안에서 호를 그리며 정오/자정에 가장 높다.
        y = int(band_h * 0.62 - math.sin(frac * math.pi) * band_h * 0.42)
        for i, r in enumerate((44, 36, 28)):
            halo = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(halo, (*glow, 45 + i * 30), (r, r), r)
            self.screen.blit(halo, (x - r, y - r))
        disc = pygame.Surface((44, 44), pygame.SRCALPHA)
        pygame.draw.circle(disc, (*color, 255), (22, 22), 20)
        self.screen.blit(disc, (x - 22, y - 22))

    def draw_weather_tint(self):
        """날씨를 화면 전체에 은은한 반투명 색으로 덧칠(하늘 밴드 대체)."""
        color = WEATHER_TINT.get(self.world.environment.weather)
        if not color:
            return
        tint = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        tint.fill(color)
        self.screen.blit(tint, (0, 0))

    def draw_ui(self):
        # 정보 패널을 '좌하단'에 둔다(상단은 하늘 띠가 차지하므로).
        ph = 92
        panel = pygame.Rect(16, self.screen_height - ph - 14,
                            min(700, self.screen_width - 32), ph)
        pygame.draw.rect(self.screen, PANEL_COLOR, panel, border_radius=8)
        pygame.draw.rect(self.screen, PANEL_BORDER, panel, 2, border_radius=8)
        env = self.world.environment
        title = f"Day {env.day}  {env.clock_text()}   Weather: {env.weather}   Temp: {env.temperature}C"
        self.screen.blit(self.title_font.render(title, True, TEXT_COLOR),
                         (panel.x + 16, panel.y + 12))
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
        panel = pygame.Rect(0, 0, min(680, self.screen_width - 48), 110)
        panel.center = (self.screen_width // 2, self.screen_height // 2)
        pygame.draw.rect(self.screen, (245, 235, 211), panel, border_radius=8)
        pygame.draw.rect(self.screen, (92, 65, 50), panel, 3, border_radius=8)
        self.label("Simulation Ended", panel.centerx, panel.centery - 22,
                   self.title_font, (62, 45, 38))
        self.label(reason, panel.centerx, panel.centery + 15, self.font, (62, 45, 38))

    def label(self, text, x, y, font, color=TEXT_COLOR):
        surface = font.render(text, True, color)
        self.screen.blit(surface, surface.get_rect(center=(x, y)))
