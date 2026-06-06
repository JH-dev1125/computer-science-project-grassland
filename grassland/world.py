# =============================================================================
# world.py — '맵' 그 자체 (역할: 사물 보관 + 한 프레임 오케스트레이션)
#
# World 가 하는 일:
#   - 동물·식물·자원·지형 목록을 보관한다.
#   - Environment(시간/날씨) 와 PhysicsEngine 인스턴스를 하나씩 들고 있다.
#   - seed_default() 로 맵에 실제 Entity(사자·얼룩말·풀 등)를 '랜덤하게' 배치한다.
#   - update(dt) 가 매 프레임 환경→동물/식물 결정→물리→후처리 순서로 지휘한다.
#   - 동물이 행동을 결정할 때 필요한 '가장 가까운 무엇' 질의를 제공한다.
# 좌표 연산은 pygame.math.Vector2 에 위임한다.
# =============================================================================
import random

from pygame.math import Vector2

from grassland.config import SEED_COUNTS, WORLD_HEIGHT, WORLD_WIDTH
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
        self._occupied = []            # (position, radius) — 큰 구조물 겹침 방지용

    # ── 초기 배치 ────────────────────────────────────────────────────────
    @classmethod
    def seed_default(cls):
        world = cls()
        world.seed_terrain()
        world.seed_plants()
        world.seed_resources()
        world.seed_animals()
        return world

    # ── 랜덤 배치 헬퍼 ───────────────────────────────────────────────────
    def _random_spot(self, margin=120):
        return Vector2(random.uniform(margin, self.width - margin),
                       random.uniform(margin, self.height - margin))

    def _find_spot(self, clearance, margin=120, tries=40):
        """이미 놓인 큰 구조물들과 clearance 이상 떨어진 빈 자리를 찾는다.
        충분히 못 찾으면 마지막 후보라도 반환(맵이 꽉 차도 멈추지 않게)."""
        spot = self._random_spot(margin)
        for _ in range(tries):
            spot = self._random_spot(margin)
            if all(spot.distance_to(pos) >= clearance + rad
                   for pos, rad in self._occupied):
                break
        return spot

    def _place(self, entity, clearance_radius=None):
        """entity 를 _occupied 에 등록해 이후 배치가 겹치지 않게 한다."""
        rad = entity.radius if clearance_radius is None else clearance_radius
        self._occupied.append((entity.position, rad))
        return entity

    def seed_terrain(self):
        # Plain: 배경(맵 전체). 이건 겹침 대상이 아니다.
        self.terrains.append(Plain(Vector2(self.width / 2, self.height / 2),
                                   max(self.width, self.height)))
        # 호숫가 1~2개, 동굴 2~3개를 서로 멀찍이 흩뿌린다.
        for _ in range(random.randint(1, 2)):
            lake = LakeSide(self._find_spot(220), size=random.uniform(70, 100))
            self.terrains.append(lake)
            self._place(lake, lake.radius)
        for _ in range(random.randint(2, 3)):
            cave = Cave(self._find_spot(180), size=random.uniform(55, 78))
            self.terrains.append(cave)
            self._place(cave, cave.radius)

    def seed_plants(self):
        # 풀: 몇 개의 '군락' 중심을 잡고 그 주변에 흩뿌려 자연스러운 패치를 만든다.
        for _ in range(random.randint(3, 5)):
            center = self._find_spot(90)
            for _ in range(random.randint(2, 4)):
                offset = Vector2(random.uniform(-110, 110), random.uniform(-110, 110))
                pos = self._clamp(center + offset, 70)
                self.plants.append(Grass(pos))
        # 덤불·아카시아·바오밥은 넓게 흩뿌린다(큰 식물끼리는 안 겹치게).
        for _ in range(random.randint(3, 5)):
            bush = Bush(self._find_spot(70))
            self.plants.append(bush)
            self._place(bush)
        for _ in range(random.randint(2, 4)):
            tree = AcaciaTree(self._find_spot(110))
            self.plants.append(tree)
            self._place(tree)
        for _ in range(random.randint(1, 2)):
            baobab = BaobabTree(self._find_spot(140))
            self.plants.append(baobab)
            self._place(baobab)

    def seed_resources(self):
        # 물웅덩이 3~5개(호숫가·서로와 떨어뜨림), 사체 1~2개(랜덤 위치).
        for _ in range(random.randint(3, 5)):
            puddle = WaterPuddle(self._find_spot(150))
            self.resources.append(puddle)
            self._place(puddle)
        for _ in range(random.randint(1, 2)):
            self.resources.append(Carcass(self._random_spot()))

    def seed_animals(self):
        """config.SEED_COUNTS 만큼 동물을 무작위 위치에 배치한다."""
        for name, count in SEED_COUNTS.items():
            cls = _ANIMAL_TYPES[name]
            for _ in range(count):
                self.animals.append(cls(self._random_spot()))

    def _clamp(self, pos, margin):
        """pos 를 맵 안(가장자리 margin)으로 강제한다."""
        return Vector2(max(margin, min(pos.x, self.width - margin)),
                       max(margin, min(pos.y, self.height - margin)))

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
        if len(grasses) >= 16:
            return
        for grass in grasses:
            if random.random() < 0.02 * dt * 60:   # 프레임레이트에 무관하게
                grass.spread_seeds()
                offset = Vector2(random.uniform(-90, 90), random.uniform(-90, 90))
                pos = self._clamp(grass.position + offset, 80)
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
        self.resources.append(Carcass(Vector2(animal.position)))

    def spawn_offspring(self, parent):
        offset = Vector2(random.uniform(-30, 30), random.uniform(-30, 30))
        pos = self._clamp(parent.position + offset, 60)
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
