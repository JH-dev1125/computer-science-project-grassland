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

from pathlib import Path

import pygame

from grassland.config import MOB_SPRITE_DIR

# 프로젝트 루트 기준으로 폴더를 찾는다(어디서 실행하든 안정적).
_BASE_DIR = Path(__file__).resolve().parent.parent
_SPRITE_DIR = _BASE_DIR / MOB_SPRITE_DIR

_originals: dict[str, pygame.Surface | None] = {}   # name → 원본(또는 None=파일없음)
_scaled: dict[tuple[str, int], pygame.Surface] = {}  # (name, 크기) → 줄인 그림


def _load_original(name: str) -> pygame.Surface | None:
    """<name>.png 를 한 번만 디스크에서 읽어 캐시. 없으면 None 을 캐시."""
    if name in _originals:
        return _originals[name]
    path = _SPRITE_DIR / f"{name}.png"
    surface: pygame.Surface | None = None
    if path.exists():
        try:
            surface = pygame.image.load(str(path)).convert_alpha()
        except pygame.error:
            surface = None
    _originals[name] = surface
    return surface


def get_sprite(name: str, size: int) -> pygame.Surface | None:
    """name 개체를 한 변 size(px) 정사각형으로 맞춘 그림을 돌려준다.
    파일이 없으면 None → 호출한 쪽이 도형으로 그리면 된다."""
    size = max(1, int(size))
    key = (name, size)
    cached = _scaled.get(key)
    if cached is not None:
        return cached
    original = _load_original(name)
    if original is None:
        return None
    scaled = pygame.transform.smoothscale(original, (size, size))
    _scaled[key] = scaled
    return scaled


def clear_cache() -> None:
    """런타임 중 이미지를 새로 넣고 다시 읽고 싶을 때 캐시를 비운다."""
    _originals.clear()
    _scaled.clear()
