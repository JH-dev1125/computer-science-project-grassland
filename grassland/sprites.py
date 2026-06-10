# =============================================================================
# sprites.py — 개체 이미지(PNG) 로더 (역할: 파일에서 그림을 읽어 캐시)
#
# gui 가 그릴 때마다 디스크에서 PNG 를 읽으면 느리다. 그래서 한 번 읽은 원본과,
# 특정 크기로 줄인 결과를 dict 에 저장(캐시)해 둔다.
#   - 파일 규칙: <개체 name 소문자>.png  (예: Lion→lion.png, Acacia_Tree→acacia_tree.png)
#   - 폴더    : config.MOB_SPRITE_DIR
#   - 이미지가 없으면 None 을 돌려준다 → gui 가 기존 도형으로 폴백.
# 이 파일은 '그림 불러오기'만 한다. 무엇을/어디에 그릴지는 gui 의 몫.
# =============================================================================
from __future__ import annotations

import math
from pathlib import Path

import pygame

from grassland.config import MOB_SPRITE_DIR

# 프로젝트 루트 기준으로 폴더를 찾는다(어디서 실행하든 안정적).
_BASE_DIR = Path(__file__).resolve().parent.parent
_SPRITE_DIR = _BASE_DIR / MOB_SPRITE_DIR
_ASSET_DIR = _BASE_DIR / "assets" / "sprites"

_loaded: dict[str, pygame.Surface | None] = {}      # 경로 → 원본(또는 None=파일없음)
_scaled: dict[tuple[str, int], pygame.Surface] = {}  # (name, 긴변) → 줄인 그림
_content_rects: dict = {}                # name → 내용(불투명) 영역 Rect (또는 None)
_content_scaled: dict = {}               # (name, size) → 내용만 잘라 크기 맞춘 그림


def _load_png(path: Path, trim_alpha: int | None = None) -> pygame.Surface | None:
    """PNG 한 장을 (경로 기준) 한 번만 디스크에서 읽어 캐시한다. 없으면 None 을 캐시.
    trim_alpha 를 주면 그림 둘레의 투명 여백을 잘라내(불투명 픽셀 영역만) 돌려준다."""
    key = str(path)
    if key in _loaded:
        return _loaded[key]
    surface: pygame.Surface | None = None
    if path.exists():
        try:
            surface = pygame.image.load(key).convert_alpha()
            if trim_alpha is not None:
                rect = surface.get_bounding_rect(min_alpha=trim_alpha)
                if rect.width > 0 and rect.height > 0:
                    surface = surface.subsurface(rect).copy()
        except pygame.error:
            surface = None
    _loaded[key] = surface
    return surface


def scale_longest(surface: pygame.Surface, size: int) -> pygame.Surface:
    """그림의 '긴 변'이 size(px) 가 되도록 가로세로 비율을 유지해 줄인다(정사각형 강제 X)."""
    size = max(1, int(size))
    w, h = surface.get_size()
    scale = size / max(w, h)
    return pygame.transform.smoothscale(
        surface, (max(1, round(w * scale)), max(1, round(h * scale))))


def _load_original(name: str) -> pygame.Surface | None:
    """<name>.png 원본(스프라이트 폴더)."""
    return _load_png(_SPRITE_DIR / f"{name}.png")


def sprite_exists(name: str) -> bool:
    """<name>.png 파일이 실제로 있는지(=로드 가능한지). 애니메이션 프레임 폴백 판정용."""
    return _load_original(name) is not None


def get_sprite(name: str, size: int) -> pygame.Surface | None:
    """name 개체의 긴 변이 size(px) 가 되도록 줄인 그림. 파일이 없으면 None."""
    key = (name, max(1, int(size)))
    cached = _scaled.get(key)
    if cached is not None:
        return cached
    original = _load_original(name)
    if original is None:
        return None
    scaled = _scaled[key] = scale_longest(original, size)
    return scaled


def _bounds(name: str):
    """그림에서 투명 여백을 뺀 '실제 그림(불투명 픽셀) 영역'의 Rect. 없으면 None.
    캔버스 크기·여백이 프레임마다 달라도, 이 영역을 기준으로 크기를 맞추면
    화면에 보이는 동물의 크기가 항상 일정해진다."""
    if name in _content_rects:
        return _content_rects[name]
    surface = _load_original(name)
    rect = None
    if surface is not None:
        r = surface.get_bounding_rect(min_alpha=12)
        if r.width > 0 and r.height > 0:
            rect = r
    _content_rects[name] = rect
    return rect


def trimmed(name: str, size: int, mode: str = "geom") -> pygame.Surface | None:
    """투명 여백을 잘라낸 뒤, '실제 그림'을 mode 기준으로 size(px)에 맞춰 비율 유지해 줄인다.
    (동물 프레임 전용. 여백이 잘려 발밑이 맨 아래에 와 anchor="bottom" 위치도 정확.)
      - "geom"  : 기하평균 √(가로×세로) = size  → 면적(덩치) 기준. 대부분의 동물에 자연스럽다.
      - "height": 세로 높이 = size            → 포즈마다 가로가 변해도 '키'가 일정.
                  (독수리처럼 날개를 폈다 접었다 해 가로폭만 달라지는 경우에 알맞다.)
      - "width" / "long": 가로 / 긴 변 기준.
    긴 변만 맞추면 포즈마다 비율이 달라 몸통이 커졌다 작아졌다 해 어색하므로 기본은 geom."""
    key = (name, max(1, int(size)), mode)
    cached = _content_scaled.get(key)
    if cached is not None:
        return cached
    original = _load_original(name)
    if original is None:
        return None
    rect = _bounds(name)
    cropped = original.subsurface(rect).copy() if rect is not None else original
    w, h = cropped.get_size()
    if mode == "height":
        ref = h
    elif mode == "width":
        ref = w
    elif mode == "long":
        ref = max(w, h)
    else:                       # "geom"
        ref = math.sqrt(w * h)
    k = max(1, int(size)) / max(1.0, ref)
    target = (max(1, round(w * k)), max(1, round(h * k)))
    scaled = _content_scaled[key] = pygame.transform.smoothscale(cropped, target)
    return scaled


def get_background():
    """초원 배경 타일 텍스처(assets/sprites/background.png). 없으면 None → 단색 초록."""
    return _load_png(_ASSET_DIR / "background.png")


def get_sky_image(name):
    """하늘 이미지(구름·해·달, assets/sprites/<name>.png). 없으면 None → 절차적 그리기."""
    return _load_png(_ASSET_DIR / f"{name}.png")


def get_weather_icon(name):
    """날씨 아이콘(assets/sprites/weather_<name>.png). 둘레 여백은 잘라낸다. 없으면 None."""
    return _load_png(_ASSET_DIR / f"weather_{name}.png", trim_alpha=24)


def clear_cache() -> None:
    """런타임 중 이미지를 새로 넣고 다시 읽고 싶을 때 캐시를 비운다."""
    for cache in (_loaded, _scaled, _content_rects, _content_scaled):
        cache.clear()
