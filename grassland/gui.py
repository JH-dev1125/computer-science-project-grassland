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
    PANEL_BORDER, PANEL_COLOR, SCREEN_HEIGHT, SCREEN_WIDTH, SPRITE_VISUAL_SCALE,
    TEXT_COLOR, WEATHER_TINT,
)
from grassland.sprites import get_sprite
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
        self.camera = Vector2(220, 180)   # 화면 좌상단이 바라보는 월드 좌표
        self.dragging = False
        self.font = self._font(17)
        self.small_font = self._font(13)
        self.title_font = self._font(22)

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
                    self.camera.x -= event.rel[0]
                    self.camera.y -= event.rel[1]
                    self.clamp_camera()
            self.world.update(dt)
            self.draw()
        pygame.quit()

    # ── 카메라 ───────────────────────────────────────────────────────────
    def clamp_camera(self):
        self.camera.x = max(0, min(self.camera.x, max(0, self.world.width - self.screen_width)))
        self.camera.y = max(0, min(self.camera.y, max(0, self.world.height - self.screen_height)))

    def resize(self, width, height):
        self.screen_width = max(MIN_SCREEN_WIDTH, width)
        self.screen_height = max(MIN_SCREEN_HEIGHT, height)
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.clamp_camera()

    def world_to_screen(self, position):
        return int(position.x - self.camera.x), int(position.y - self.camera.y)

    def visible(self, entity, margin=120):
        x, y = self.world_to_screen(entity.position)
        return -margin <= x <= self.screen_width + margin and \
               -margin <= y <= self.screen_height + margin

    # ── 스프라이트(이미지) 그리기 ────────────────────────────────────────
    def blit_sprite(self, entity, x, y):
        """entity 의 PNG 를 (x,y) 중심에 그린다.
        크기는 충돌 반지름 × 종류별 표시 배율 × 개체별 draw_scale 로 정한다.
        이미지를 못 찾으면(파일명 오타 등) 자주색 점만 찍어 '여기 그림이 없다'를
        알려 준다 — 디버그용 최소 안전장치."""
        scale = SPRITE_VISUAL_SCALE.get(entity.kind, 2.2)
        size = int(entity.radius * 2 * scale * entity.draw_scale)
        sprite = get_sprite(entity.name.lower(), size)
        if sprite is None:
            pygame.draw.circle(self.screen, (210, 60, 210),
                               (x, y), max(4, int(entity.radius * 0.4)))
            return
        if getattr(entity, "is_hidden", False):   # 숨으면 반투명하게
            sprite = sprite.copy()
            sprite.set_alpha(130)
        self.screen.blit(sprite, sprite.get_rect(center=(x, y)))

    # ── 그리기(아래 레이어 → 위 레이어 순서) ─────────────────────────────
    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)   # 평원 배경
        self.draw_grid()
        self.draw_terrains()                 # 지형(맨 아래)
        self.draw_plants()
        self.draw_resources()
        self.draw_animals()
        self.draw_weather_tint()             # 날씨 틴트(개체 위, UI 아래)
        self.draw_ui()                       # 정보 패널(맨 위)
        pygame.display.flip()

    def draw_grid(self):
        cam = self.camera
        start_x = int(cam.x // 80) * 80
        start_y = int(cam.y // 80) * 80
        for wx in range(start_x, int(cam.x + self.screen_width) + 80, 80):
            sx = int(wx - cam.x)
            pygame.draw.line(self.screen, GRID_COLOR, (sx, 0), (sx, self.screen_height), 1)
        for wy in range(start_y, int(cam.y + self.screen_height) + 80, 80):
            sy = int(wy - cam.y)
            pygame.draw.line(self.screen, GRID_COLOR, (0, sy), (self.screen_width, sy), 1)

    def draw_terrains(self):
        for terrain in self.world.terrains:
            if terrain.name == "Plain":      # 배경은 fill 로 이미 처리
                continue
            if not self.visible(terrain, 200):
                continue
            x, y = self.world_to_screen(terrain.position)
            r = int(terrain.radius)
            self.blit_sprite(terrain, x, y)
            self.label(terrain.name, x, y + r + 8, self.small_font)

    def draw_plants(self):
        for plant in self.world.alive_plants():
            if not self.visible(plant):
                continue
            x, y = self.world_to_screen(plant.position)
            size = int(plant.radius * 1.45)
            self.blit_sprite(plant, x, y)
            self.label(plant.name, x, y + size // 2 + 10, self.small_font)

    def draw_resources(self):
        for resource in self.world.resources:
            if not resource.alive or not self.visible(resource):
                continue
            x, y = self.world_to_screen(resource.position)
            r = int(resource.radius)
            self.blit_sprite(resource, x, y)
            self.label(resource.name, x, y + r + 10, self.small_font)

    def draw_animals(self):
        for animal in self.world.animals:
            if not animal.alive or not self.visible(animal):
                continue
            x, y = self.world_to_screen(animal.position)
            size = int(animal.radius * 2)
            self.blit_sprite(animal, x, y)
            self.health_bar(animal, x, y - size // 2 - 9, size)
            self.label(animal.name, x, y + size // 2 + 9, self.small_font)
            if animal.action_text:
                self.label(animal.action_text, x, y - size // 2 - 22,
                           self.small_font, (36, 36, 32))

    def health_bar(self, animal, x, y, width):
        bar = pygame.Rect(0, 0, max(24, width), 5); bar.center = (x, y)
        pygame.draw.rect(self.screen, (80, 65, 58), bar)
        fill = bar.copy()
        fill.width = int(bar.width * max(0.0, animal.health / max(1.0, animal.max_health)))
        pygame.draw.rect(self.screen, (88, 190, 91), fill)

    def draw_weather_tint(self):
        """날씨를 화면 전체에 은은한 반투명 색으로 덧칠(하늘 밴드 대체)."""
        color = WEATHER_TINT.get(self.world.environment.weather)
        if not color:
            return
        tint = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        tint.fill(color)
        self.screen.blit(tint, (0, 0))

    def draw_ui(self):
        panel = pygame.Rect(16, 14, min(700, self.screen_width - 32), 92)
        pygame.draw.rect(self.screen, PANEL_COLOR, panel, border_radius=8)
        pygame.draw.rect(self.screen, PANEL_BORDER, panel, 2, border_radius=8)
        env = self.world.environment
        title = f"Day {env.day}  {env.clock_text()}   Weather: {env.weather}   Temp: {env.temperature}C"
        self.screen.blit(self.title_font.render(title, True, TEXT_COLOR), (32, 26))
        counts = self.world.counts_by_name()
        ctext = " | ".join(f"{n}:{c}" for n, c in sorted(counts.items()))
        self.screen.blit(self.font.render(ctext, True, TEXT_COLOR), (32, 58))
        cam = f"Map {int(self.camera.x)},{int(self.camera.y)} / drag to move"
        self.screen.blit(self.small_font.render(cam, True, TEXT_COLOR), (32, 83))
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
