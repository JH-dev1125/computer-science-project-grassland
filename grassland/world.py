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

from grassland.config import (
    SEED_COUNTS, WORLD_HEIGHT, WORLD_WIDTH,
    SPRITE_DISPLAY_SIZE, SPRITE_DISPLAY_DEFAULT,
    MEERKAT_ENDING_DAY, MEERKAT_GROW_PER_SEC)
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
        self.meerkat_ending = False    # 미어캣 엔딩(거대 미어캣이 모든 것을 잠식) 진행 중

    # ── 초기 배치 ────────────────────────────────────────────────────────
    @classmethod
    def seed_default(cls):
        world = cls()
        world.seed_structures()   # 큰 구조물: 격자 셀에 한 개씩(겹침 0 보장)
        world.seed_grass()        # 풀: 구조물 위는 피해서 빽빽이
        world.seed_carcasses()
        world.seed_animals()
        return world

    # ── 랜덤 배치 헬퍼 ───────────────────────────────────────────────────
    def _spot(self, margin=50):
        return Vector2(random.uniform(margin, self.width - margin),
                       random.uniform(margin, self.height - margin))

    def _radius(self, name):
        """화면에 그려지는 '시각적' 반지름. 표시 크기의 절반."""
        return SPRITE_DISPLAY_SIZE.get(name, SPRITE_DISPLAY_DEFAULT) / 2.0

    def seed_structures(self):
        """큰 구조물(호숫가·동굴·나무·덤불·물웅덩이)을 '격자 셀'에 한 개씩 배치한다.
        각 구조물은 자기 셀을 벗어나지 않게(셀-크기-시각크기 만큼만 흔들림) 두므로,
        셀끼리 안 겹치는 한 구조물도 절대 안 겹친다 → 겹침 0 보장 + 골고루 분포."""
        self.terrains.append(Plain(Vector2(self.width / 2, self.height / 2),
                                   max(self.width, self.height)))
        cell = 200                                  # 셀을 줄여 구조물이 맵 전체에 더 골고루 퍼지게 함
        cols = max(1, int(self.width // cell))
        rows = max(1, int(self.height // cell))
        cell_w, cell_h = self.width / cols, self.height / rows
        cells = [((c + 0.5) * cell_w, (r + 0.5) * cell_h)
                 for r in range(rows) for c in range(cols)]
        random.shuffle(cells)

        # 가로로 왼쪽/가운데/오른쪽 3구역으로 나눠 두고, 각 종류의 구조물을
        # '구역을 한 바퀴씩 돌아가며' 뽑아 배치한다 → 특정 종류가 한쪽에 몰리는 것을 방지.
        thirds = (0, self.width / 3.0, 2 * self.width / 3.0, self.width)
        buckets = []
        for i in range(3):
            lo, hi = thirds[i], thirds[i + 1]
            bucket = [c for c in cells if lo <= c[0] < hi]
            random.shuffle(bucket)
            buckets.append(bucket)
        region_order = [0, 1, 2]
        random.shuffle(region_order)
        region_turn = [0]   # 리스트에 담아 closure 안에서 값 변경(증가) 가능하게 함

        def pick_cells(n):
            """다음 n개의 셀을, 구역(왼쪽→가운데→오른쪽 순서를 섞은 순환)을 돌며 고른다.
            그러면 같은 종류의 구조물이 여러 개일 때 자연히 맵 전역에 퍼진다."""
            picked = []
            for _ in range(n):
                for _try in range(3):
                    region = region_order[region_turn[0] % 3]
                    region_turn[0] += 1
                    if buckets[region]:
                        picked.append(buckets[region].pop())
                        break
                else:
                    if cells:
                        picked.append(cells.pop())
            return picked

        # 종류별로 미리 개수를 정하고, 위 순환 방식으로 위치를 배정한다
        # (모든 큰 구조물을 같은 방식으로 다뤄 어떤 종류든 한쪽에 쏠리지 않게 함)
        plan = [
            ("Lake_Side", lambda p: LakeSide(p, size=random.uniform(75, 95)), self.terrains,
             random.randint(2, 3)),
            ("Cave", lambda p: Cave(p, size=random.uniform(90, 105)), self.terrains,
             random.randint(2, 3)),
            ("Acacia_Tree", AcaciaTree, self.plants, random.randint(7, 9)),
            ("Baobab_Tree", BaobabTree, self.plants, random.randint(4, 6)),
            ("Water_Puddle", WaterPuddle, self.resources, random.randint(0, 1)),
            ("Bush", Bush, self.plants, random.randint(3, 5)),
        ]

        all_specs = []
        all_cells = []
        for name, make, target, want in plan:
            got = pick_cells(want)
            all_specs.extend([(name, make, target)] * len(got))
            all_cells.extend(got)

        # 남은 빈 셀도 채워 맵 전체에 빈자리가 없게 한다(덤불/물웅덩이 위주, 나무·동굴 과밀 방지)
        remaining = [c for region in buckets for c in region] + cells
        for c in remaining:
            extra_kind = random.choices(
                [("Bush", Bush, self.plants),
                 ("Water_Puddle", WaterPuddle, self.resources),
                 None],   # 빈 셀로 남겨 둬, 덤불이 과하게 채워지지 않게 함(풀이 대신 자랄 자리)
                weights=[3, 1, 11],
            )[0]
            if extra_kind is None:
                continue
            all_specs.append(extra_kind)
            all_cells.append(c)

        gap = 14.0   # 큰 구조물끼리 최소 이만큼은 떨어뜨려, 시각적으로 겹치지 않게 함
        for (name, make, target), (cx, cy) in zip(all_specs, all_cells):
            vis = self._radius(name) * 2             # 시각 지름
            jx = max(0.0, (cell_w - vis) / 2 - 8)   # 셀을 벗어나지 않는 흔들림 한계
            jy = max(0.0, (cell_h - vis) / 2 - 8)
            my_r = self._radius(name)
            pos = None
            for _try in range(20):
                cand = self._clamp(Vector2(cx + random.uniform(-jx, jx),
                                           cy + random.uniform(-jy, jy)), 40)
                if all(cand.distance_to(p) >= my_r + rad + gap for p, rad in self._occupied):
                    pos = cand
                    break
            if pos is None:
                continue   # 겹치지 않는 자리를 못 찾으면 이 구조물은 건너뜀(겹침 0 유지)
            ent = make(pos)
            target.append(ent)
            self._occupied.append((ent.position, my_r))

    def _blocked(self, pos, extra=38):
        """pos 가 이미 놓인 구조물의 시각 범위 + 여유(extra) 안인가.
        extra 는 풀·덤불 스프라이트의 시각 반지름(≈35px)만큼 더해,
        경계선 바로 바깥에 생성해도 이미지가 구조물과 겹치지 않게 한다."""
        return any(pos.distance_to(p) < rad + extra for p, rad in self._occupied)

    def _side_spot(self, margin=30):
        """가장자리(좌/우)에 더 잘 걸리는 무작위 위치. 풀을 양옆으로 퍼뜨려 동물이
        중앙에만 몰리지 않게 한다(70%는 바깥 1/3, 30%만 중앙)."""
        if random.random() < 0.85:   # 85%는 바깥 1/3(좌·우)에 — 중앙 쏠림 방지
            x = (random.uniform(margin, self.width * 0.33) if random.random() < 0.5
                 else random.uniform(self.width * 0.67, self.width - margin))
        else:
            x = random.uniform(self.width * 0.33, self.width * 0.67)
        return Vector2(x, random.uniform(margin, self.height - margin))

    def _on_water(self, pos, pad=44):
        """pos 가 물(웅덩이·호숫가) 위/근처인가 — 풀이 물과 겹치지 않게 한다.
        (비로 새로 생긴 웅덩이까지 포함하도록 _occupied 가 아니라 현재 물을 직접 본다.)"""
        for w in self.water_puddles():
            if pos.distance_to(w.position) < w.radius + pad:
                return True
        for t in self.terrains:
            if isinstance(t, LakeSide) and pos.distance_to(t.position) < t.radius + pad:
                return True
        return False

    def _grass_blocked(self, pos):
        return self._blocked(pos) or self._on_water(pos)

    def _spawn_grass_cluster(self, center, count=None):
        """중심 둘레로 5~7 포기만 '원형'으로 모은 자연스러운 풀 덩어리(일자 X, 과밀 X)."""
        count = count or random.randint(5, 7)
        base_ang = random.uniform(0.0, 360.0)
        for i in range(count):
            ang = base_ang + 360.0 * i / count + random.uniform(-22.0, 22.0)
            off = Vector2(random.uniform(22.0, 50.0), 0.0).rotate(ang)
            pos = self._clamp(center + off, 18)
            if not self._grass_blocked(pos):
                self.plants.append(Grass(pos))

    def seed_grass(self):
        """풀: 중앙은 듬성듬성 1~2 포기, 사이드는 5~7 포기 원형 군집 몇 개."""
        # 1) 중앙 — 듬성듬성 1~2 포기씩 넓게 흩뿌림
        for _ in range(random.randint(6, 9)):
            c = Vector2(random.uniform(self.width * 0.34, self.width * 0.66),
                        random.uniform(30, self.height - 30))
            for _ in range(random.randint(1, 2)):
                pos = self._clamp(c + Vector2(random.uniform(-24, 24),
                                              random.uniform(-24, 24)), 18)
                if not self._grass_blocked(pos):
                    self.plants.append(Grass(pos))
        # 2) 사이드 — 5~7 포기 원형 군집 몇 개
        for _ in range(random.randint(4, 6)):
            self._spawn_grass_cluster(self._side_spot(45))

    def seed_carcasses(self):
        for _ in range(random.randint(2, 3)):
            self.resources.append(Carcass(self._spot()))

    def seed_animals(self):
        """config.SEED_COUNTS 만큼 동물을 무작위 위치에 배치한다."""
        for name, count in SEED_COUNTS.items():
            cls = _ANIMAL_TYPES[name]
            for _ in range(count):
                self.animals.append(cls(self._spot()))

    def _clamp(self, pos, margin):
        """pos 를 맵 안(가장자리 margin)으로 강제한다."""
        return Vector2(max(margin, min(pos.x, self.width - margin)),
                       max(margin, min(pos.y, self.height - margin)))

    def obstacles(self):
        """동물이 통과 못 하는 '벽' 목록 (위치, 막는 반지름).
        나무(아카시아·바오밥), 물(호숫가·물웅덩이), 동굴이 벽 — 풀·덤불은 통과 가능."""
        obs = []
        for p in self.plants:
            if p.alive and isinstance(p, (AcaciaTree, BaobabTree)):
                obs.append((p.position, p.radius))
        for t in self.terrains:
            if isinstance(t, LakeSide):
                obs.append((t.position, t.radius))
            # Cave 는 apply_terrain_effects() 에서 can_enter 기반으로 처리하므로
            # 여기서는 제외 — 두 시스템이 동시에 밀면 경계에서 '비벼짐' 현상이 생긴다.
        for r in self.resources:
            if r.alive and isinstance(r, WaterPuddle):
                obs.append((r.position, r.radius))
        return obs

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
            animal.is_hidden = False
            animal.interaction_target = None
            if getattr(animal, '_bounce_timer', 0.0) > 0.0:
                animal._bounce_timer = max(0.0, animal._bounce_timer - dt)
            animal.update(self, dt)
        # 4) 물리: 조향 이동(분리·회피·가장자리) + 지형 효과
        living = self.living_animals()
        self.physics.update(living, self.obstacles(), dt)   # 나무·물가 = 구조물(회피·통과불가)
        self.physics.apply_terrain_effects(living, self.terrains)
        self._elephant_bounce(living)
        self.apply_weather_effects(living, dt)   # 더위·비 등 날씨가 동물 수치에 영향
        # 5) 자원 갱신 + 후처리(번식·사망 정리)
        for resource in self.resources:
            resource.update(self, dt)
        self.update_meerkat_ending(dt)        # 미어캣 엔딩(거대화·잠식) 진행
        if not self.meerkat_ending:           # 잠식 중엔 풀 재생·일반 번식 정지(잠식 완료 가능)
            self.regrow_plants(dt)
            self.try_reproduce()
        self.flush_pending()
        self.check_end_conditions()

    def apply_weather_effects(self, living, dt):
        """날씨·온도가 동물 전반에 주는 영향:
        - 더울수록(heat_factor) 갈증이 빨리 차고 기력 회복이 더뎌 쉽게 지친다.
        - 가뭄(폭염)엔 체력이 닳지만, '잎이 무성한 나무 그늘' 아래면 더위를 피한다.
        - 비·흐림(선선)엔 체력이 천천히 회복된다."""
        env = self.environment
        heat = env.heat_factor()
        shade_trees = [p for p in self.plants if p.alive
                       and isinstance(p, (AcaciaTree, BaobabTree)) and p.has_foliage()]
        for a in living:
            in_shade = False
            if env.weather == "drought":
                for t in shade_trees:
                    if a.position.distance_to(t.position) <= t.radius + a.radius + 30:
                        t.provide_shade(a)
                        in_shade = True
                        break
            if heat > 0.0 and not in_shade:
                a.thirst = min(100.0, a.thirst + heat * 1.4 * dt)
                a.stamina = max(0.0, a.stamina - heat * 2.0 * dt)
            if env.weather == "drought" and not in_shade:
                a.health = max(1.0, a.health - 0.6 * dt)
            elif env.weather in ("rain", "cloudy"):
                a.health = min(a.max_health, a.health + 0.5 * dt)

    def apply_environment_events(self, dt):
        if self.environment.weather == "drought":
            if self.drought_event is None:
                self.drought_event = DroughtEvent(random.uniform(0.5, 1.0))
            self.drought_event.dry_up_map(self, dt)
            return
        self.drought_event = None
        if self.environment.weather == "rain":
            # 비: 호숫가 물이 불고, 웅덩이도 차오르며, 가끔 새 웅덩이가 생긴다.
            for lake in [t for t in self.terrains if isinstance(t, LakeSide)]:
                lake.fill_rain(8.0 * dt)
            for puddle in self.water_puddles():
                puddle.regenerate(6.0 * dt)
            if len(self.water_puddles()) < 8 and random.random() < 0.02 * dt * 60:
                self._spawn_puddle()

    def _spawn_puddle(self):
        pos = self._clamp(self._side_spot(40), 30)
        if self._blocked(pos):
            return
        puddle = WaterPuddle(pos, amount=random.uniform(60.0, 100.0))
        self.resources.append(puddle)
        # 새로 고인 물에 잠긴 풀은 사라진다(풀이 물 위로 비치지 않게).
        for g in self.plants:
            if g.alive and g.name == "Grass" and g.position.distance_to(pos) < puddle.radius:
                g.die()

    def on_new_day(self):
        if self.environment.weather == "rain":
            for puddle in self.water_puddles():
                puddle.fill_rain()

    def regrow_plants(self, dt):
        """살아있는 풀이 씨앗을 퍼뜨려 가끔 주변에 새 풀이 자란다(계획서 spread_seeds).
        풀 공급이 끊겨 초원이 사막화되는 것을 막는다. 전체 풀 수는 상한으로 제한."""
        grasses = [p for p in self.plants if p.alive and p.name == "Grass"]
        if len(grasses) >= 85:                 # 상한 더 낮춰 듬성듬성 유지(과밀·물겹침 방지)
            return
        growth = self.environment.growth_multiplier()
        if random.random() >= 0.9 * dt * growth:   # 천천히(≈초당 0.9·growth회만 시도)
            return
        # 분포 유지: 대개 '사이드 군집' 근처에 돋아 군집을 살리고, 가끔만 중앙에 1포기.
        if random.random() < 0.18:
            pos = Vector2(random.uniform(self.width * 0.34, self.width * 0.66),
                          random.uniform(40, self.height - 40))
        else:
            side = [g for g in grasses
                    if g.position.x < self.width * 0.33 or g.position.x > self.width * 0.67]
            if side:
                parent = random.choice(side)
                off = Vector2(random.uniform(28.0, 70.0), 0.0).rotate(random.uniform(0, 360))
                pos = parent.position + off
            else:
                pos = self._side_spot(30)
        pos = self._clamp(pos, 18)
        m = 40.0
        if not (m <= pos.x <= self.width - m and m <= pos.y <= self.height - m):
            return
        if not self._grass_blocked(pos):
            self.plants.append(Grass(pos))

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

    def _elephant_bounce(self, living):
        """사자·하이에나가 코끼리에 닿으면 평면 상에서 이동 반대 방향으로 튕겨낸다."""
        elephants = [a for a in living if a.name == "Elephant"]
        for elephant in elephants:
            for other in living:
                if other.name not in ("Lion", "Hyena"):
                    continue
                if elephant.position.distance_to(other.position) >= elephant.radius + other.radius + 4:
                    continue
                v = other.velocity
                if v.length_squared() > 4.0:
                    bounce_dir = -v.normalize()
                else:
                    away = other.position - elephant.position
                    bounce_dir = away.normalize() if away.length_squared() > 1e-6 else Vector2(1, 0)
                power = other.speed * 1.4
                other.velocity = bounce_dir * power
                other.desired_velocity = bounce_dir * power

    def update_meerkat_ending(self, dt):
        """MEERKAT_ENDING_DAY 를 넘기면 미어캣들이 서서히 거대해지며(크기·체력·공격·속도)
        모든 동물·식물·나무를 잡아먹는다. 잠식이 진행되는 '연출'을 위해 점진적으로 성장한다."""
        meerkats = [a for a in self.living_animals() if a.name == "Meerkat"]
        if not meerkats:
            return
        if self.environment.day < MEERKAT_ENDING_DAY:
            # 엔딩 전: 크기만 아주 조금씩 커진다(스탯·행동 변화 없음)
            for m in meerkats:
                m.draw_scale = min(1.4, m.draw_scale + dt * 0.006)
            return
        self.meerkat_ending = True
        for m in meerkats:
            m.apocalypse = True
            g = min(1.0, getattr(m, "_grow", 0.0) + dt * MEERKAT_GROW_PER_SEC)  # 0→1 서서히
            m._grow = g
            m.draw_scale = 1.4 + g * 3.1       # 화면 크기 최대 ~4.5배(이전 7배에서 축소)
            m.radius = 13.0 + g * 40.0
            m.power = 5.0 + g * 55.0
            m.speed = 82.0 + g * 60.0
            m.detect_range = 130.0 + g * 550.0
            m.max_health = 42.0 + g * 450.0
            m.health = m.max_health            # 잠식자는 무적에 가깝게 — 굶거나 지치지 않음
            m.hunger = m.thirst = 0.0
            m.stamina = 100.0

    def check_end_conditions(self):
        # 미어캣 엔딩: 거대 미어캣이 다른 모든 동물·식물(나무 포함)을 잠식하면 종료
        if self.meerkat_ending:
            others = [a for a in self.living_animals() if a.name != "Meerkat"]
            if not others and not self.alive_plants():
                self.environment.ended = True
                self.environment.end_reason = "미어캣이 초원의 모든 것을 집어삼켰습니다 - 미어캣 엔딩"

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

    def nearest_plant(self, position, max_distance=None):
        return self._nearest(self.plants, position, max_distance=max_distance)

    def nearest_bush(self, position, max_distance):
        return self._nearest(self.plants, position,
                             lambda p: isinstance(p, Bush), max_distance)

    def nearest_tree(self, position, max_distance=None, need_foliage=False):
        """가장 가까운 나무(아카시아·바오밥). need_foliage 면 잎이 충분한 나무만."""
        def ok(p):
            if not isinstance(p, (AcaciaTree, BaobabTree)):
                return False
            return p.has_foliage() if need_foliage else True
        return self._nearest(self.plants, position, ok, max_distance)

    def nearest_carcass(self, position, max_distance=None):
        return self._nearest(self.carcasses(), position,
                             lambda c: c.carried_by is None, max_distance)

    def nearest_water(self, position, max_distance=None):
        candidates = list(self.water_puddles()) + \
            [t for t in self.terrains if isinstance(t, LakeSide)]
        return self._nearest(candidates, position, max_distance=max_distance)

    def nearest_weak_or_prey(self, hunter, max_distance):
        """잡식(혹멧돼지)의 사냥 대상: 탐지범위 안의 초식·잡식, 또는 '약한' 육식(체력 50%↓).
        코끼리와 같은 종, 자기 자신은 제외."""
        def ok(a):
            if a is hunter or a.name == hunter.name or a.name == "Elephant":
                return False
            if a.diet_type in ("herbivore", "omnivore"):
                return True
            return a.diet_type == "carnivore" and a.health < a.max_health * 0.5
        return self._nearest(self.animals, hunter.position, ok, max_distance)

    def nearest_predator(self, animal, max_distance):
        # 덤불에 숨은(is_hidden) 포식자는 피식자에게 보이지 않는다 → 기습 성립
        return self._nearest(self.animals, animal.position,
                             lambda a: a is not animal and a.diet_type == "carnivore"
                                       and not a.is_hidden,
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

    def nearest_devour_target(self, meerkat):
        """미어캣 엔딩용: 미어캣이 먹어 치울 가장 가까운 대상(자기 외 모든 동물 + 모든 식물·나무)."""
        prey = self._nearest(self.animals, meerkat.position,
                             lambda a: a is not meerkat and a.name != "Meerkat")
        plant = self._nearest(self.plants, meerkat.position)
        cands = [c for c in (prey, plant) if c is not None]
        if not cands:
            return None
        return min(cands, key=lambda c: meerkat.position.distance_to(c.position))

    def nearest_terrain_type(self, terrain_name, position):
        return self._nearest(self.terrains, position,
                             lambda t: t.name == terrain_name)
