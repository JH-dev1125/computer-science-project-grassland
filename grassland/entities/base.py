from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from itertools import count
from typing import Tuple

from grassland.geometry import Vec2

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from grassland.world import World

Color = Tuple[int, int, int]
_ENTITY_IDS = count(1)


@dataclass
class Entity(ABC):
    name: str
    position: Vec2
    radius: float
    color: Color
    velocity: Vec2 = field(default_factory=Vec2)
    alive: bool = True
    solid: bool = True
    render_shape: str = "square"
    action_text: str = ""
    kind: str = "entity"
    id: int = field(default_factory=lambda: next(_ENTITY_IDS), init=False)

    def update(self, world: "World", dt: float) -> None:
        return None

    def distance_to(self, other: "Entity") -> float:
        return self.position.distance_to(other.position)

    def is_near(self, target: "Entity", range_value: float) -> bool:
        return self.distance_to(target) <= range_value

    def move_toward(self, target: Vec2, speed: float) -> None:
        self.velocity = (target - self.position).normalized() * speed

    def move_away_from(self, target: Vec2, speed: float) -> None:
        self.velocity = (self.position - target).normalized() * speed

    def stop(self) -> None:
        self.velocity = Vec2()

    def status(self) -> str:
        state = "alive" if self.alive else "dead"
        return f"{self.name}: {state} at ({self.position.x:.0f}, {self.position.y:.0f})"
