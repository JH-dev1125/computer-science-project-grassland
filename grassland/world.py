# =============================================================================
# world.py — '맵' 그 자체 (역할: 사물 보관 + 한 프레임 오케스트레이션)
#
# World 가 하는 일:
#   - 동물·식물·자원·지형 목록을 보관한다.
#   - Environment(시간/날씨) 와 PhysicsEngine 인스턴스를 하나씩 들고 있다.
#   - seed_default() 로 맵에 실제 Entity(사자·얼룩말·풀 등)를 배치한다.
#   - update(dt) 가 매 프레임 환경→동물/식물 결정→물리→후처리 순서로 지휘한다.
#   - 동물이 행동을 결정할 때 필요한 '가장 가까운 무엇' 질의를 제공한다.
# World 는 Environment 를 정의하지 않고(→ environment.py), 그리지도 않는다(→ gui).
# =============================================================================
import random

from grassland.config import SEED_COUNTS, WORLD_HEIGHT, WORLD_WIDTH
from grassland.geometry import Vec2
from grassland.physics import PhysicsEngine
from grassland.environment import Environment, DroughtEvent

from grassland.entities.animals import (
    Lion, Hyena, BaldEagle, Zebra, Gazelle, Elephant, Meerkat, Warthog)
from grassland.entities.plants import Grass, Bush, AcaciaTree, BaobabTree
from grassland.entities.terrain import Plain, LakeSide, Cave
from grassland.entities.resources import WaterPuddle, Carcass

# 이름 → 생성자 (seed 에 사용)
_ANIMAL_TYPES = {
    "Lion": Lion, "Hyena": Hyena, "Bald_Eagle": BaldEagle,
    "Zebra": Zebra, "Gazelle": Gazelle, "Elephant": Elephant,
    "Meerkat": Meerkat, "Warthog": Warthog,
}


class World:
    def __init__(self, width=WORLD_WIDTH, height=WORLD_HEIGHT):
        self.width = width
        self.height = height
        self.environment = Environment()
        self.physics = PhysicsEngine(width, height)
        self.elapsed = 0.0
        self.animals = []
        self.plants = []
        self.resources = []
        self.terrains = []
        self.drought_event = None
        self._pending_animals = []     # 이번 프레임에 태어난 새끼(끝나고 합침)

    # ── 초기 배치 ────────────────────────────────────────────────────────
    @classmethod
    def seed_default(cls):
        world = cls()
        world.seed_terrain()
        world.seed_plants()
        world.seed_resources()
        world.seed_animals()
        return world

    def seed_terrain(self):
        # Plain: 배경(맵 전체). Lake_Side·Cave 는 서로 멀리 떨어뜨려 겹치지 않게 배치.
        self.terrains.append(Plain(Vec2(self.width / 2, self.height / 2),
                                   max(self.width, self.height)))
        self.terrains.append(LakeSide(Vec2(360, 320)))
        self.terrains.append(Cave(Vec2(1980, 1240)))

    def seed_plants(self):
        for pos in [(560, 360), (820, 520), (1180, 470), (1500, 760), (2050, 560)]:
            self.plants.append(Grass(Vec2(*pos)))
        self.plants.append(Bush(Vec2(980, 300)))
        self.plants.append(Bush(Vec2(1650, 1050)))
        self.plants.append(AcaciaTree(Vec2(720, 980)))
        self.plants.append(BaobabTree(Vec2(1350, 1180)))

    def seed_resources(self):
        # 물웅덩이는 호숫가와 떨어진 곳에 둔다(겹침 방지).
        self.resources.append(WaterPuddle(Vec2(1500, 320)))
        self.resources.append(WaterPuddle(Vec2(900, 1300)))
        self.resources.append(Carcass(Vec2(1200, 700)))

    def seed_animals(self):
        """config.SEED_COUNTS 만큼 동물을 무작위 위치에 배치한다."""
        for name, count in SEED_COUNTS.items():
            cls = _ANIMAL_TYPES[name]
            for _ in range(count):
                self.animals.append(cls(self._random_spot()))

    def _random_spot(self):
        return Vec2(random.uniform(120, self.width - 120),
                    random.uniform(120, self.height - 120))

    # ── 매 프레임 갱신 ───────────────────────────────────────────────────
    def update(self, dt):
        if self.environment.ended:
            return
        self.elapsed += dt

        # 1) 환경(시간·날씨)
        if self.environment.update(dt):
            self.on_new_day()
        # 2) 환경 이벤트(가뭄) 적용
        self.apply_environment_events(dt)
        # 3) 식물·동물의 자체 변화 + 행동 결정
        for plant in self.plants:
            plant.update(self, dt)
        for animal in self.animals:
            animal.update(self, dt)
        # 4) 물리: 충돌 분리 + 이동 + 맵 경계, 그리고 지형 효과
        living = self.living_animals()
        self.physics.update(living, dt)
        self.physics.apply_terrain_effects(living, self.terrains)
        # 5) 자원 갱신 + 후처리(번식·사망 정리)
        for resource in self.resources:
            resource.update(self, dt)
        self.regrow_plants(dt)
        self.try_reproduce()
        self.flush_pending()
        self.check_end_conditions()

    def apply_environment_events(self, dt):
        if self.environment.weather == "drought":
            if self.drought_event is None:
                self.drought_event = DroughtEvent(random.uniform(0.5, 1.0))
            self.drought_event.dry_up_map(self, dt)
        else:
            self.drought_event = None

    def on_new_day(self):
        if self.environment.weather == "rain":
            for puddle in self.water_puddles():
                puddle.fill_rain()

    def regrow_plants(self, dt):
        """살아있는 풀이 씨앗을 퍼뜨려 가끔 주변에 새 풀이 자란다(계획서 spread_seeds).
        풀 공급이 끊겨 초원이 사막화되는 것을 막는다. 전체 풀 수는 상한으로 제한."""
        grasses = [p for p in self.plants if p.alive and p.name == "Grass"]
        if len(grasses) >= 12:
            return
        for grass in grasses:
            if random.random() < 0.02 * dt * 60:   # 프레임레이트에 무관하게
                grass.spread_seeds()
                offset = Vec2(random.uniform(-90, 90), random.uniform(-90, 90))
                pos = (grass.position + offset).clamp(
                    80, 80, self.width - 80, self.height - 80)
                self.plants.append(Grass(pos))
                break

    def try_reproduce(self):
        """피식자/잡식이 안전·포만 상태이고 같은 종이 가까우면 낮은 확률로 번식."""
        for animal in self.living_animals():
            # 잘 먹고(배고픔/갈증 낮고) 쫓기지 않을 때만 번식 (육식/초식/잡식 공통)
            if animal.hunger > 45 or animal.thirst > 45:
                continue
            if getattr(animal, "is_chased", False):
                continue
            cap = 8 if animal.diet_type == "carnivore" else 14  # 포식자 상한은 낮게
            if len([a for a in self.animals if a.alive and a.name == animal.name]) >= cap:
                continue
            mate = self.nearest_same_species(animal, 60.0)
            if mate is not None and random.random() < 0.0015:
                if animal.couple(animal, mate):
                    self.spawn_offspring(animal)

    def flush_pending(self):
        if self._pending_animals:
            self.animals.extend(self._pending_animals)
            self._pending_animals = []

    def check_end_conditions(self):
        # 가뭄이 3일 이상 이어져 물이 마르면 종료
        if self.environment.weather == "drought" and self.environment.day >= 3:
            if sum(p.amount for p in self.water_puddles()) <= 2:
                self.environment.ended = True
                self.environment.end_reason = "가뭄으로 물이 말라 생태계가 종료되었습니다."

    # ── 생성/사망 ────────────────────────────────────────────────────────
    def spawn_carcass(self, animal):
        self.resources.append(Carcass(animal.position.copy()))

    def spawn_offspring(self, parent):
        offset = Vec2(random.uniform(-30, 30), random.uniform(-30, 30))
        pos = (parent.position + offset).clamp(60, 60, self.width - 60, self.height - 60)
        self._pending_animals.append(_ANIMAL_TYPES[parent.name](pos))

    # ── 컬렉션 질의 ──────────────────────────────────────────────────────
    def living_animals(self):
        return [a for a in self.animals if a.alive]

    def alive_plants(self):
        return [p for p in self.plants if p.alive]

    def water_puddles(self):
        return [r for r in self.resources if isinstance(r, WaterPuddle) and r.alive]

    def carcasses(self):
        return [r for r in self.resources if isinstance(r, Carcass) and r.alive]

    def counts_by_name(self):
        counts = {}
        for animal in self.living_animals():
            counts[animal.name] = counts.get(animal.name, 0) + 1
        return counts

    # ── nearest 질의 (행동 결정에 필요한 '사실' 제공) ────────────────────
    def _nearest(self, items, position, predicate=None, max_distance=None):
        best, nearest = float("inf"), None
        for item in items:
            if not item.alive:
                continue
            if predicate is not None and not predicate(item):
                continue
            d = position.distance_to(item.position)
            if max_distance is not None and d > max_distance:
                continue
            if d < best:
                best, nearest = d, item
        return nearest

    def nearest_plant(self, position):
        return self._nearest(self.plants, position)

    def nearest_bush(self, position, max_distance):
        return self._nearest(self.plants, position,
                             lambda p: isinstance(p, Bush), max_distance)

    def nearest_carcass(self, position):
        return self._nearest(self.carcasses(), position,
                             lambda c: c.carried_by is None)

    def nearest_water(self, position):
        candidates = list(self.water_puddles()) + \
            [t for t in self.terrains if isinstance(t, LakeSide)]
        return self._nearest(candidates, position)

    def nearest_predator(self, animal, max_distance):
        return self._nearest(self.animals, animal.position,
                             lambda a: a is not animal and a.diet_type == "carnivore",
                             max_distance)

    def nearest_prey_for(self, predator, max_distance):
        # 코끼리(Elephant)는 몸집이 커 사냥 대상에서 제외 — 접근 시 stomp 로 쫓겨난다.
        return self._nearest(self.animals, predator.position,
                             lambda a: a is not predator and a.name != "Elephant"
                                       and a.diet_type in ("herbivore", "omnivore"),
                             max_distance)

    def nearest_named(self, name, position, max_distance):
        return self._nearest(self.animals, position,
                             lambda a: a.name == name, max_distance)

    def nearest_same_species(self, animal, radius):
        return self._nearest(self.animals, animal.position,
                             lambda a: a is not animal and a.name == animal.name, radius)

    def nearest_terrain_type(self, terrain_name, position):
        return self._nearest(self.terrains, position,
                             lambda t: t.name == terrain_name)
