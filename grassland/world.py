from __future__ import annotations

import random
from typing import Callable, Optional, TypeVar

from grassland.config import DAY_LENGTH_HOURS
from grassland.config import GAME_HOURS_PER_SECOND
from grassland.config import WORLD_HEIGHT
from grassland.config import WORLD_WIDTH
from grassland.geometry import Vec2
from grassland.physics import PhysicsEngine
from grassland.entities.base import Entity
from grassland.entities.animals.animal import Animal
from grassland.entities.plants.plant import Plant
from grassland.entities.plants.grass import Grass
from grassland.entities.plants.bush import Bush
from grassland.entities.plants.acacia_tree import AcaciaTree
from grassland.entities.plants.baobab_tree import BaobabTree
from grassland.entities.terrain.terrain_base import Terrain
from grassland.entities.terrain.plain import Plain
from grassland.entities.terrain.lake_side import LakeSide
from grassland.entities.terrain.cave import Cave
from grassland.entities.resources.resource import Resource
from grassland.entities.resources.water_puddle import WaterPuddle
from grassland.entities.resources.carcass import Carcass

_E = TypeVar("_E", bound=Entity)


class Environment:
    def __init__(self) -> None:
        self.day: int = 1
        self.time: float = 6.0
        self.weather: str = "sunny"
        self.temperature: int = 28
        self.ended: bool = False
        self.end_reason: str = ""

    def update(self, dt: float) -> bool:
        previous_day = self.day
        self.change_time(dt * GAME_HOURS_PER_SECOND)
        return self.day != previous_day

    def change_time(self, hours: float) -> None:
        self.time += hours
        while self.time >= DAY_LENGTH_HOURS:
            self.time -= DAY_LENGTH_HOURS
            self.change_day()

    def change_day(self) -> None:
        self.day += 1
        self.change_weather()
        self.change_temperature()

    def change_weather(self) -> None:
        self.weather = random.choice(["sunny", "cloudy", "rain", "drought"])

    def change_temperature(self) -> None:
        if self.weather == "drought":
            self.temperature = random.randint(34, 42)
        elif self.weather == "rain":
            self.temperature = random.randint(20, 28)
        elif self.weather == "cloudy":
            self.temperature = random.randint(23, 31)
        else:
            self.temperature = random.randint(27, 36)

    def clock_text(self) -> str:
        hour = int(self.time)
        minute = int((self.time - hour) * 60)
        return str(hour).zfill(2) + ":" + str(minute).zfill(2)


class DroughtEvent:
    def __init__(self, drought_intensity: float) -> None:
        self.drought_intensity = drought_intensity

    def dry_up_map(self, world: World, dt: float) -> None:
        for puddle in world.water_puddles():
            puddle.consume(dt * self.drought_intensity * 3.0)


class World:
    def __init__(self, width: int = WORLD_WIDTH, height: int = WORLD_HEIGHT) -> None:
        self.width = width
        self.height = height
        self.environment = Environment()
        self.physics = PhysicsEngine(width, height)
        self.elapsed: float = 0.0
        self.animals: list[Animal] = []
        self.plants: list[Plant] = []
        self.resources: list[Resource] = []
        self.terrains: list[Terrain] = []
        self.drought_event: Optional[DroughtEvent] = None

    @classmethod
    def seed_default(cls) -> World:
        world = cls()
        world.seed_terrain()
        world.seed_plants()
        world.seed_resources()
        return world

    def seed_terrain(self) -> None:
        self.terrains.append(Plain(Vec2(self.width / 2, self.height / 2), max(self.width, self.height)))
        self.terrains.append(LakeSide(Vec2(310, 260)))
        self.terrains.append(Cave(Vec2(1470, 890)))

    def seed_plants(self) -> None:
        self.plants.append(Grass(Vec2(520, 300)))
        self.plants.append(Grass(Vec2(780, 360)))
        self.plants.append(Grass(Vec2(1080, 460)))
        self.plants.append(Bush(Vec2(900, 260)))
        self.plants.append(AcaciaTree(Vec2(760, 660)))
        self.plants.append(BaobabTree(Vec2(1010, 930)))

    def seed_resources(self) -> None:
        self.resources.append(WaterPuddle(Vec2(410, 360)))
        self.resources.append(WaterPuddle(Vec2(1330, 980)))
        self.resources.append(Carcass(Vec2(1120, 540)))

    def update(self, dt: float) -> None:
        if self.environment.ended:
            return

        self.elapsed += dt
        if self.environment.update(dt):
            self.on_new_day()

        if self.environment.weather == "drought":
            if self.drought_event is None:
                self.drought_event = DroughtEvent(random.uniform(0.5, 1.0))
            self.drought_event.dry_up_map(self, dt)
        else:
            self.drought_event = None

        for plant in self.plants:
            plant.update(self, dt)
        for animal in self.animals:
            animal.update(self, dt)
        self.physics.update(self.living_animals(), dt)
        for resource in self.resources:
            resource.update(self, dt)

        self.check_end_conditions()

    def on_new_day(self) -> None:
        if self.environment.weather == "rain":
            for puddle in self.water_puddles():
                puddle.fill_rain()

    def check_end_conditions(self) -> None:
        if self.environment.weather == "drought" and self.environment.day >= 3:
            if sum(p.amount for p in self.water_puddles()) <= 2:
                self.environment.ended = True
                self.environment.end_reason = "가뭄으로 물이 말라 생태계가 종료되었습니다."

    def spawn_carcass(self, animal: Animal) -> None:
        self.resources.append(Carcass(Vec2(animal.position.x, animal.position.y)))

    # ── 컬렉션 쿼리 ────────────────────────────────────────────────────────────

    def living_animals(self) -> list[Animal]:
        return [a for a in self.animals if a.alive]

    def alive_plants(self) -> list[Plant]:
        return [p for p in self.plants if p.alive]

    def water_puddles(self) -> list[WaterPuddle]:
        return [r for r in self.resources if isinstance(r, WaterPuddle) and r.alive]

    def carcasses(self) -> list[Carcass]:
        return [r for r in self.resources if isinstance(r, Carcass) and r.alive]

    # ── nearest 쿼리 ───────────────────────────────────────────────────────────

    def nearest_alive(
        self,
        items: list[_E],
        position: Vec2,
        predicate: Optional[Callable[[_E], bool]] = None,
        max_distance: Optional[float] = None,
    ) -> Optional[_E]:
        nearest: Optional[_E] = None
        best = float("inf")
        for item in items:
            if not item.alive:
                continue
            if predicate is not None and not predicate(item):
                continue
            d = position.distance_to(item.position)
            if max_distance is not None and d > max_distance:
                continue
            if d < best:
                best = d
                nearest = item
        return nearest

    def nearest_plant(self, position: Vec2) -> Optional[Plant]:
        return self.nearest_alive(self.plants, position)

    def nearest_bush(self, position: Vec2, max_distance: float) -> Optional[Bush]:
        bushes = [p for p in self.plants if isinstance(p, Bush)]
        return self.nearest_alive(bushes, position, max_distance=max_distance)

    def nearest_carcass(self, position: Vec2) -> Optional[Carcass]:
        return self.nearest_alive(
            self.carcasses(), position,
            lambda c: c.carried_by is None,
        )

    def nearest_water(self, position: Vec2) -> Optional[WaterPuddle | LakeSide]:
        candidates: list[WaterPuddle | LakeSide] = [
            *self.water_puddles(),
            *(t for t in self.terrains if isinstance(t, LakeSide)),
        ]
        return self.nearest_alive(candidates, position)

    def nearest_predator(self, animal: Animal, max_distance: float) -> Optional[Animal]:
        return self.nearest_alive(
            self.animals, animal.position,
            lambda a: a is not animal and a.diet_type == "carnivore",
            max_distance,
        )

    def nearest_prey_for(self, predator: Animal, max_distance: float) -> Optional[Animal]:
        return self.nearest_alive(
            self.animals, predator.position,
            lambda a: a is not predator and a.diet_type in ("herbivore", "omnivore"),
            max_distance,
        )

    def nearest_named(self, name: str, position: Vec2, max_distance: float) -> Optional[Animal]:
        return self.nearest_alive(
            self.animals, position,
            lambda a: a.name == name,
            max_distance,
        )

    def nearest_same_species(self, animal: Animal, radius: float) -> Optional[Animal]:
        return self.nearest_alive(
            self.animals, animal.position,
            lambda a: a is not animal and a.name == animal.name,
            radius,
        )

    def nearest_terrain_type(self, terrain_name: str, position: Vec2) -> Optional[Terrain]:
        return self.nearest_alive(
            self.terrains, position,
            lambda t: t.name == terrain_name,
        )

    def carcass_eaten_by_lion_near(self, position: Vec2, max_distance: float) -> Optional[Carcass]:
        return self.nearest_alive(
            self.carcasses(), position,
            lambda c: c.being_eaten_by is not None and c.being_eaten_by.name == "Lion",
            max_distance,
        )

    # ── 기타 ───────────────────────────────────────────────────────────────────

    def spawn_offspring(self, parent: Animal) -> None:
        offset = Vec2(random.uniform(-30, 30), random.uniform(-30, 30))
        new_pos = Vec2(
            max(0.0, min(float(self.width), parent.position.x + offset.x)),
            max(0.0, min(float(self.height), parent.position.y + offset.y)),
        )
        try:
            # 구체 서브클래스(Gazelle 등)는 position 하나만 받는 생성자를 가짐
            self.animals.append(type(parent)(new_pos))  # type: ignore[call-arg]
        except Exception:
            pass

    def expel_meerkats_from_cave(self, cave: Cave) -> None:
        for animal in self.living_animals():
            if animal.name == "Meerkat" and cave.contains(animal):
                animal.move_away_from(cave.position, animal.speed * 1.3)
                animal.action_text = "expelled"
                animal.is_hidden = False

    def current_drought_intensity(self) -> float:
        if self.environment.weather != "drought" or self.drought_event is None:
            return 0.0
        return self.drought_event.drought_intensity

    def counts_by_name(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for animal in self.living_animals():
            counts[animal.name] = counts.get(animal.name, 0) + 1
        return counts
