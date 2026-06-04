# =============================================================================
# geometry.py — 순수 2D 벡터 수학 (역할: 수·벡터 연산만)
# Vec2 로 위치·속도·방향을 표현. Entity·world·pygame 을 전혀 모른다.
# 의존 방향: physics → geometry (그 반대 없음).
# =============================================================================
import math
import random


class Vec2:
    """2차원 벡터 (x, y)."""
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def __add__(self, other):  return Vec2(self.x + other.x, self.y + other.y)
    def __sub__(self, other):  return Vec2(self.x - other.x, self.y - other.y)
    def __mul__(self, value):  return Vec2(self.x * value, self.y * value)   # 스칼라 곱
    __rmul__ = __mul__

    def __truediv__(self, value):
        if value == 0:
            return Vec2()
        return Vec2(self.x / value, self.y / value)

    def copy(self):
        return Vec2(self.x, self.y)

    def length(self):
        """벡터 길이 √(x²+y²)."""
        return math.sqrt(self.x * self.x + self.y * self.y)

    def normalized(self):
        """길이 1의 방향 벡터 (길이 0이면 제로벡터)."""
        size = self.length()
        if size <= 0.0001:
            return Vec2()
        return self / size

    def distance_to(self, other):
        """두 점 사이 직선 거리."""
        return (self - other).length()

    def limit(self, max_length):
        """길이를 max_length 로 제한(방향 유지)."""
        size = self.length()
        if size > max_length and size > 0:
            return self.normalized() * max_length
        return self.copy()

    def clamp(self, min_x, min_y, max_x, max_y):
        """x,y 를 범위 안으로 강제(맵 이탈 방지)."""
        return Vec2(max(min_x, min(self.x, max_x)),
                    max(min_y, min(self.y, max_y)))

    def as_int_tuple(self):
        return int(self.x), int(self.y)


def random_unit_vector():
    """무작위 방향 단위벡터."""
    angle = random.uniform(0, math.tau)
    return Vec2(math.cos(angle), math.sin(angle))
