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
#
#  [실행 흐름에서의 위치 — 가장 중요한 파일]
#    app.run() 이 World.seed_default() 로 이 클래스를 만들고,
#    gui 의 매 프레임 루프가 world.update(dt) 를 끝없이 부른다.
#    즉 '맵에 무엇을 놓을지(seed_*)' 와 '매 순간 무슨 일이 일어날지(update)' 가 여기 다 있다.
#
#  [이 파일을 읽는 두 갈래]
#    (A) 게임 시작 시 1번만:  seed_default → seed_structures → seed_grass
#                                          → seed_carcasses → seed_animals
#    (B) 매 프레임 반복:      update → (환경) → (식물/동물 update) → (물리) → (후처리)
# =============================================================================
import random  # [문법] 표준 라이브러리. 무작위 위치/확률(번식 등)에 쓴다.

# [문법] pygame.math.Vector2 : 2차원 벡터(x, y). 좌표·이동·거리 계산을 직접 구현하지 않고
#        이 클래스에 위임한다(예: a.distance_to(b), v.normalize()).
from pygame.math import Vector2

# [흐름 0] 아래 import 들은 app.py 가 world 를 불러올 때 '한 번' 실행되어
#          config 상수와 물리·환경·엔티티 클래스들을 메모리에 올린다.
from grassland.config import (
    SEED_COUNTS, WORLD_HEIGHT, WORLD_WIDTH,
    SPRITE_DISPLAY_SIZE, SPRITE_DISPLAY_DEFAULT,
    MEERKAT_ENDING_DAY, MEERKAT_GROW_PER_SEC)
from grassland.physics import PhysicsEngine          # 이동·충돌 담당(update 4단계에서 사용)
from grassland.environment import Environment, DroughtEvent  # 시간·날씨(update 1단계에서 사용)

# 동물·식물·지형·자원 클래스들(seed 와 isinstance 판정에 사용)
from grassland.entities.animals import (
    Lion, Hyena, BaldEagle, Zebra, Gazelle, Elephant, Meerkat, Warthog)
from grassland.entities.plants import Grass, Bush, AcaciaTree, BaobabTree
from grassland.entities.terrain import Plain, LakeSide, Cave
from grassland.entities.resources import WaterPuddle, Carcass

# [변수] _ANIMAL_TYPES : '종 이름 → 그 종을 만드는 클래스' 표.
#        seed_animals() 와 spawn_offspring() 이 이름만 알고도 객체를 만들게 해 준다.
# [문법] 맨 앞 밑줄(_ANIMAL_TYPES) : '이 모듈 내부에서만 쓰는 것'이라는 관례적 표시(private).
_ANIMAL_TYPES = {
    "Lion": Lion, "Hyena": Hyena, "Bald_Eagle": BaldEagle,
    "Zebra": Zebra, "Gazelle": Gazelle, "Elephant": Elephant,
    "Meerkat": Meerkat, "Warthog": Warthog,
}


class World:
    def __init__(self, width=WORLD_WIDTH, height=WORLD_HEIGHT):
        # [←호출] seed_default() 안에서 cls() 형태로 호출된다(아래).
        # [변수] width/height : 맵의 크기(기본은 config 의 WORLD_WIDTH/HEIGHT).
        self.width = width
        self.height = height
        self.environment = Environment()              # [변수] 시간·날씨 시스템(매 프레임 갱신)
        self.physics = PhysicsEngine(width, height)   # [변수] 이동·충돌 엔진(매 프레임 사용)
        self.elapsed = 0.0                            # [변수] 시작 후 누적된 실제 시간(초)
        self.animals = []                             # [변수] 모든 동물 목록(죽은 것도 잠시 포함)
        self.plants = []                              # [변수] 모든 식물 목록
        self.resources = []                           # [변수] 자원(물웅덩이·사체) 목록
        self.terrains = []                            # [변수] 지형(평원·동굴·호숫가) 목록
        self.drought_event = None                     # [변수] 현재 진행 중인 가뭄 이벤트(없으면 None)
        self._pending_animals = []     # [변수] 이번 프레임에 태어난 새끼(루프 중 목록 변형 방지용 임시 보관)
        self._occupied = []            # [변수] (위치, 반지름) — 큰 구조물 겹침 방지용 점유 목록
        self.meerkat_ending = False    # [변수] 미어캣 엔딩(거대 미어캣이 모든 것을 잠식) 진행 중 여부

    # ── 초기 배치 ────────────────────────────────────────────────────────
    @classmethod
    def seed_default(cls):
        # [←호출] app.run() 이 'World.seed_default()' 로 부른다(게임 시작 시 1번).
        # [문법] @classmethod + 첫 인자 cls : 인스턴스 없이 클래스로 호출하는 메서드.
        #        cls 는 World 클래스 자신을 가리키므로 cls() == World() 다(팩토리 패턴).
        # [흐름 A-1] 빈 World 를 만든 뒤, 아래 순서대로 맵을 채운다(순서가 중요).
        world = cls()
        world.seed_structures()   # [호출→] (A-2) 큰 구조물: 격자 셀에 한 개씩(겹침 0 보장)
        world.seed_grass()        # [호출→] (A-3) 풀: 구조물 위는 피해서 빽빽이
        world.seed_carcasses()    # [호출→] (A-4) 사체 몇 개
        world.seed_animals()      # [호출→] (A-5) SEED_COUNTS 만큼 동물 배치
        return world              # 완성된 맵을 app.run() 에 돌려준다

    # ── 랜덤 배치 헬퍼 ───────────────────────────────────────────────────
    def _spot(self, margin=50):
        """맵 안 무작위 한 점(가장자리에서 margin 만큼 안쪽)을 돌려준다."""
        # [문법] random.uniform(a, b) : a~b 사이 실수 난수.
        return Vector2(random.uniform(margin, self.width - margin),
                       random.uniform(margin, self.height - margin))

    def _radius(self, name):
        """화면에 그려지는 '시각적' 반지름. 표시 크기의 절반."""
        # [문법] dict.get(key, default) : 키가 있으면 그 값, 없으면 default 를 돌려준다(KeyError 회피).
        return SPRITE_DISPLAY_SIZE.get(name, SPRITE_DISPLAY_DEFAULT) / 2.0

    def seed_structures(self):
        """큰 구조물(호숫가·동굴·나무·덤불·물웅덩이)을 '격자 셀'에 한 개씩 배치한다.
        각 구조물은 자기 셀을 벗어나지 않게(셀-크기-시각크기 만큼만 흔들림) 두므로,
        셀끼리 안 겹치는 한 구조물도 절대 안 겹친다 → 겹침 0 보장 + 골고루 분포."""
        # [←호출] seed_default() (A-2)
        # 맵 전체를 덮는 배경 지형 Plain 을 먼저 깐다(효과 없음, 그냥 바탕).
        self.terrains.append(Plain(Vector2(self.width / 2, self.height / 2),
                                   max(self.width, self.height)))
        cell = 200                                  # [변수] 격자 한 칸의 크기(px). 작을수록 더 골고루 퍼짐
        cols = max(1, int(self.width // cell))      # [변수] 가로 셀 개수 (// = 몫만 취하는 나눗셈)
        rows = max(1, int(self.height // cell))     # [변수] 세로 셀 개수
        cell_w, cell_h = self.width / cols, self.height / rows  # [변수] 실제 셀 한 칸의 가로/세로
        # [변수] cells : 모든 셀의 '중심 좌표' 목록.
        # [문법] [식 for r in ... for c in ...] : 리스트 컴프리헨션(이중 반복). 셀 중심들을 한 번에 만든다.
        cells = [((c + 0.5) * cell_w, (r + 0.5) * cell_h)
                 for r in range(rows) for c in range(cols)]
        random.shuffle(cells)   # 셀 순서를 섞어 무작위로 뽑게 한다

        # 가로로 왼쪽/가운데/오른쪽 3구역으로 나눠 두고, 각 종류의 구조물을
        # '구역을 한 바퀴씩 돌아가며' 뽑아 배치한다 → 특정 종류가 한쪽에 몰리는 것을 방지.
        thirds = (0, self.width / 3.0, 2 * self.width / 3.0, self.width)  # [변수] 3구역 경계 x값
        buckets = []   # [변수] buckets[0/1/2] = 좌/중/우 구역에 속한 셀들
        for i in range(3):
            lo, hi = thirds[i], thirds[i + 1]
            bucket = [c for c in cells if lo <= c[0] < hi]  # 이 구역 x범위에 든 셀만 추림
            random.shuffle(bucket)
            buckets.append(bucket)
        region_order = [0, 1, 2]     # [변수] 구역을 도는 순서(아래에서 섞는다)
        random.shuffle(region_order)
        region_turn = [0]   # [변수] 지금 몇 번째로 구역을 뽑을 차례인가.
        # [문법] 값 하나를 '리스트에 담아' 두는 이유: 아래 중첩 함수(closure) 안에서 이 값을
        #        '증가'시켜야 하는데, 일반 정수는 안쪽 함수에서 바깥 값을 못 바꾼다(재할당 불가).
        #        리스트의 원소(region_turn[0])는 바꿀 수 있어 카운터로 쓴다.

        def pick_cells(n):
            """다음 n개의 셀을, 구역(왼쪽→가운데→오른쪽 순서를 섞은 순환)을 돌며 고른다.
            그러면 같은 종류의 구조물이 여러 개일 때 자연히 맵 전역에 퍼진다."""
            # [문법] 함수 안에 정의된 함수 = '중첩 함수(closure)'. 바깥의 buckets/region_order 등을
            #        그대로 읽어 쓸 수 있어 인자를 길게 넘길 필요가 없다.
            picked = []
            for _ in range(n):
                for _try in range(3):    # 최대 3번 시도(빈 구역이면 다음 구역으로)
                    region = region_order[region_turn[0] % 3]   # 이번 차례의 구역
                    region_turn[0] += 1                         # 차례를 하나 넘긴다(카운터 증가)
                    if buckets[region]:
                        picked.append(buckets[region].pop())    # 그 구역에서 셀 하나 빼서 채택
                        break
                else:
                    # [문법] for ... else : for 가 'break 없이' 끝났을 때만 실행된다.
                    #        세 구역이 다 비었으면 전체 cells 에서라도 하나 뽑는다.
                    if cells:
                        picked.append(cells.pop())
            return picked

        # 종류별로 미리 개수를 정하고, 위 순환 방식으로 위치를 배정한다
        # (모든 큰 구조물을 같은 방식으로 다뤄 어떤 종류든 한쪽에 쏠리지 않게 함)
        # [변수] plan : (이름, 만드는 함수, 넣을 목록, 개수) 튜플들의 목록.
        # [문법] lambda p: ... : 이름 없는 한 줄 함수. 위치 p 를 받아 구조물 객체를 만들어 돌려준다.
        plan = [
            ("Lake_Side", lambda p: LakeSide(p, size=random.uniform(75, 95)), self.terrains,
             random.randint(2, 3)),
            ("Cave", lambda p: Cave(p, size=random.uniform(90, 105)), self.terrains,
             random.randint(3, 5)),
            ("Acacia_Tree", AcaciaTree, self.plants, random.randint(7, 9)),
            ("Baobab_Tree", BaobabTree, self.plants, random.randint(4, 6)),
            ("Water_Puddle", WaterPuddle, self.resources, random.randint(0, 1)),
            ("Bush", Bush, self.plants, random.randint(3, 5)),
        ]

        all_specs = []   # [변수] 각 구조물의 (이름, 만드는 함수, 넣을 목록)
        all_cells = []   # [변수] 각 구조물이 들어갈 셀 중심 좌표
        for name, make, target, want in plan:
            got = pick_cells(want)                                 # want 개의 셀을 골라
            all_specs.extend([(name, make, target)] * len(got))   # 그 수만큼 spec 을 늘리고
            all_cells.extend(got)                                  # 셀 좌표도 함께 모은다

        # 남은 빈 셀도 채워 맵 전체에 빈자리가 없게 한다(덤불/물웅덩이 위주, 나무·동굴 과밀 방지)
        remaining = [c for region in buckets for c in region] + cells
        for c in remaining:
            # [문법] random.choices(목록, weights=가중치)[0] : 가중치 비율대로 하나를 뽑는다.
            #        None 의 가중치를 크게(11) 둬 대부분의 빈 셀은 '비워' 풀이 자랄 자리로 남긴다.
            extra_kind = random.choices(
                [("Bush", Bush, self.plants),
                 ("Water_Puddle", WaterPuddle, self.resources),
                 None],
                weights=[3, 1, 11],
            )[0]
            if extra_kind is None:
                continue   # 이 셀은 비워 둔다
            all_specs.append(extra_kind)
            all_cells.append(c)

        gap = 14.0   # [변수] 큰 구조물끼리 최소 이만큼은 떨어뜨려 시각적으로 안 겹치게 함
        # [문법] zip(A, B) : 두 목록을 짝지어 (a, b) 로 함께 돈다.
        for (name, make, target), (cx, cy) in zip(all_specs, all_cells):
            vis = self._radius(name) * 2             # [변수] 이 구조물의 시각 지름
            jx = max(0.0, (cell_w - vis) / 2 - 8)   # [변수] 셀을 벗어나지 않는 가로 흔들림 한계
            jy = max(0.0, (cell_h - vis) / 2 - 8)   # [변수] 세로 흔들림 한계
            my_r = self._radius(name)               # [변수] 이 구조물의 시각 반지름
            pos = None
            for _try in range(20):    # 겹치지 않는 자리를 최대 20번 시도
                cand = self._clamp(Vector2(cx + random.uniform(-jx, jx),
                                           cy + random.uniform(-jy, jy)), 40)
                # [문법] all(조건 for ...) : 모든 항목이 조건을 만족하면 True.
                #        이미 놓인 모든 구조물과 충분히 떨어졌는지 검사한다.
                if all(cand.distance_to(p) >= my_r + rad + gap for p, rad in self._occupied):
                    pos = cand
                    break
            if pos is None:
                continue   # 자리를 못 찾으면 이 구조물은 건너뜀(겹침 0 유지)
            ent = make(pos)                              # 위치 pos 에 실제 구조물 객체 생성
            target.append(ent)                           # 알맞은 목록(terrains/plants/resources)에 추가
            self._occupied.append((ent.position, my_r))  # 점유 목록에 등록(다음 배치가 피하도록)

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
            # [문법] isinstance(x, 클래스) : x 가 그 클래스(또는 자식)인지 검사.
            if isinstance(t, LakeSide) and pos.distance_to(t.position) < t.radius + pad:
                return True
        return False

    def _grass_blocked(self, pos):
        """풀을 심으면 안 되는 자리인가(구조물 위 또는 물 위)."""
        return self._blocked(pos) or self._on_water(pos)

    def _spawn_grass_cluster(self, center, count=None):
        """중심 둘레로 5~7 포기만 '원형'으로 모은 자연스러운 풀 덩어리(일자 X, 과밀 X)."""
        count = count or random.randint(5, 7)   # [문법] A or B : A가 거짓(None/0)이면 B 사용
        base_ang = random.uniform(0.0, 360.0)   # [변수] 군집을 도는 시작 각도
        for i in range(count):
            ang = base_ang + 360.0 * i / count + random.uniform(-22.0, 22.0)  # 고르게 분산 + 약간 흔들기
            # [문법] Vector2(r, 0).rotate(각도) : 길이 r 의 벡터를 각도만큼 회전 → 중심에서의 오프셋
            off = Vector2(random.uniform(22.0, 50.0), 0.0).rotate(ang)
            pos = self._clamp(center + off, 18)
            if not self._grass_blocked(pos):
                self.plants.append(Grass(pos))

    def seed_grass(self):
        """풀: 중앙은 듬성듬성 1~2 포기, 사이드는 5~7 포기 원형 군집 몇 개."""
        # [←호출] seed_default() (A-3)
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
        """사체 2~3개를 무작위 위치에 둔다(시작부터 분해자가 먹을거리 제공)."""
        # [←호출] seed_default() (A-4)
        for _ in range(random.randint(2, 3)):
            self.resources.append(Carcass(self._spot()))

    def _spot_near_cave(self, max_dist=200):
        """굴(Cave) 반경 max_dist 이내 무작위 위치. 굴이 없으면 일반 _spot()."""
        caves = [t for t in self.terrains if isinstance(t, Cave)]
        if not caves:
            return self._spot()
        cave = random.choice(caves)
        angle = random.uniform(0.0, 360.0)
        dist = random.uniform(25.0, max_dist)
        return self._clamp(cave.position + Vector2(dist, 0.0).rotate(angle), 30)

    def seed_animals(self):
        """config.SEED_COUNTS 만큼 동물을 무작위 위치에 배치한다."""
        # [←호출] seed_default() (A-5) — 동물 배치는 구조물·풀 다음(미어캣이 굴 옆에 서도록)
        # [문법] dict.items() : 딕셔너리를 (키, 값) 쌍으로 하나씩 돈다.
        for name, count in SEED_COUNTS.items():
            cls = _ANIMAL_TYPES[name]   # 이름으로 클래스를 찾는다(예: "Lion" → Lion)
            for _ in range(count):
                # 미어캣만 굴 근처에, 나머지는 아무 데나.
                pos = self._spot_near_cave(200) if name == "Meerkat" else self._spot()
                self.animals.append(cls(pos))   # [호출→] 각 종 클래스의 __init__(position)

    def _clamp(self, pos, margin):
        """pos 를 맵 안(가장자리 margin)으로 강제한다."""
        # [문법] max(a, min(x, b)) : x 를 a~b 사이로 '집어 넣는' 관용구(clamp).
        return Vector2(max(margin, min(pos.x, self.width - margin)),
                       max(margin, min(pos.y, self.height - margin)))

    def obstacles(self):
        """동물이 통과 못 하는 '벽' 목록 (위치, 막는 반지름).
        나무(아카시아·바오밥), 물(호숫가·물웅덩이), 동굴이 벽 — 풀·덤불은 통과 가능."""
        # [←호출] update() 4단계에서 physics.update(..., self.obstacles(), ...) 로 매 프레임 호출.
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
        # [←호출] gui.run() 의 메인 루프가 매 프레임 'world.update(sim_dt)' 로 부른다(흐름 B).
        # [변수] dt : 이번 프레임에서 흐른 시간(초). 배속/일시정지가 반영된 값.
        # [흐름 B-0] 시뮬레이션이 끝났으면(미어캣 엔딩 등) 아무것도 안 한다.
        if self.environment.ended:
            return
        self.elapsed += dt

        # 1) 환경(시간·날씨)
        # [흐름 B-1] [호출→] environment.update(dt) : 시간을 진행한다. 하루가 넘어가면 True.
        if self.environment.update(dt):
            self.on_new_day()       # 날짜가 바뀐 순간의 처리(비 오면 물 채움)
        # 2) 환경 이벤트(가뭄) 적용
        # [흐름 B-2] [호출→] apply_environment_events(dt) : 가뭄이면 물 마름 / 비면 물 참
        self.apply_environment_events(dt)
        # 3) 식물·동물의 자체 변화 + 행동 결정
        # [흐름 B-3] 각 식물·동물이 스스로 update 한다(스탯 변화 + '무엇을 할지' 결정).
        for plant in self.plants:
            plant.update(self, dt)          # [호출→] Plant.update (광합성으로 체력 회복 등)
        for animal in self.animals:
            animal.is_hidden = False        # 매 프레임 은신 상태 초기화(이번 프레임에 다시 정해짐)
            animal.interaction_target = None
            # [변수] _bounce_timer : 코끼리 짓밟기 등으로 '통통 튀는' 모션이 남은 시간. 줄여 나간다.
            if getattr(animal, '_bounce_timer', 0.0) > 0.0:
                animal._bounce_timer = max(0.0, animal._bounce_timer - dt)
            # [호출→] Animal.update → behave() : 여기서 동물이 desired_velocity(가고 싶은 속도)만 정한다.
            animal.update(self, dt)
        # 4) 물리: 조향 이동(분리·회피·가장자리) + 지형 효과
        living = self.living_animals()      # [변수] 살아있는 동물만(죽은 것은 물리 제외)
        # [흐름 B-4] [호출→] physics.update(살아있는동물, 벽목록, dt) : 실제 위치를 움직이고 겹침을 푼다.
        self.physics.update(living, self.obstacles(), dt)   # 나무·물가 = 구조물(회피·통과불가)
        self.physics.apply_terrain_effects(living, self.terrains)  # 동굴·호숫가 '원 안 효과'
        self._elephant_bounce(living)       # 코끼리에 닿은 사자·하이에나 튕겨내기
        self.apply_weather_effects(living, dt)   # 더위·비 등 날씨가 동물 수치에 영향
        # 5) 자원 갱신 + 후처리(번식·사망 정리)
        for resource in self.resources:
            resource.update(self, dt)       # [호출→] Carcass.update(부패) 등
        self.update_meerkat_ending(dt)      # 미어캣 엔딩(거대화·잠식) 진행
        if not self.meerkat_ending:         # 잠식 중엔 풀 재생·일반 번식 정지(잠식 완료 가능)
            self.regrow_plants(dt)          # 풀이 씨앗으로 번져 새 풀이 자람
            self.try_reproduce()            # 동물 번식
        self.flush_pending()                # 이번 프레임 태어난 새끼를 animals 에 합침
        self.check_end_conditions()         # 종료 조건(미어캣 엔딩 완성) 검사

    def apply_weather_effects(self, living, dt):
        """날씨·온도가 동물 전반에 주는 영향:
        - 더울수록(heat_factor) 갈증이 빨리 차고 기력 회복이 더뎌 쉽게 지친다.
        - 가뭄(폭염)엔 체력이 닳지만, '잎이 무성한 나무 그늘' 아래면 더위를 피한다.
        - 비·흐림(선선)엔 체력이 천천히 회복된다."""
        # [←호출] update() 4단계 끝.
        env = self.environment
        heat = env.heat_factor()    # [변수] 더위 강도(0~). 26도에서 0, 더울수록 커짐.
        # [변수] shade_trees : 잎이 무성한 나무들(그늘 제공 가능).
        shade_trees = [p for p in self.plants if p.alive
                       and isinstance(p, (AcaciaTree, BaobabTree)) and p.has_foliage()]
        for a in living:
            in_shade = False
            if env.weather == "drought":
                for t in shade_trees:
                    if a.position.distance_to(t.position) <= t.radius + a.radius + 30:
                        t.provide_shade(a)   # 그늘 효과(스트레스↓)
                        in_shade = True
                        break
            if heat > 0.0 and not in_shade:
                a.thirst = min(100.0, a.thirst + heat * 1.4 * dt)   # 더우면 갈증↑
                a.stamina = max(0.0, a.stamina - heat * 1.0 * dt)   # 더우면 기력↓
            if env.weather == "drought" and not in_shade:
                a.health = max(1.0, a.health - 0.6 * dt)            # 가뭄+그늘 밖 → 체력↓
            elif env.weather in ("rain", "cloudy"):
                a.health = min(a.max_health, a.health + 0.5 * dt)   # 선선하면 체력 회복

    def apply_environment_events(self, dt):
        """가뭄이면 물을 말리고, 비면 물을 채운다(+가끔 새 웅덩이)."""
        # [←호출] update() 2단계.
        if self.environment.weather == "drought":
            if self.drought_event is None:
                self.drought_event = DroughtEvent(random.uniform(0.5, 1.0))  # 가뭄 강도 정하기
            self.drought_event.dry_up_map(self, dt)   # [호출→] DroughtEvent.dry_up_map(물 마름)
            return
        self.drought_event = None   # 가뭄이 아니면 이벤트 해제
        if self.environment.weather == "rain":
            # 비: 호숫가 물이 불고, 웅덩이도 차오르며, 가끔 새 웅덩이가 생긴다.
            for lake in [t for t in self.terrains if isinstance(t, LakeSide)]:
                lake.fill_rain(8.0 * dt)
            for puddle in self.water_puddles():
                puddle.regenerate(6.0 * dt)
            if len(self.water_puddles()) < 8 and random.random() < 0.02 * dt * 60:
                self._spawn_puddle()

    def _spawn_puddle(self):
        """비 올 때 가끔 새 물웅덩이를 만든다(풀이 잠기면 그 풀은 사라짐)."""
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
        """날짜가 막 바뀌었을 때 1회 처리(비 오는 날이면 웅덩이 채움)."""
        # [←호출] update() 1단계에서 environment.update() 가 True 를 줄 때.
        if self.environment.weather == "rain":
            for puddle in self.water_puddles():
                puddle.fill_rain()

    def regrow_plants(self, dt):
        """살아있는 풀이 씨앗을 퍼뜨려 가끔 주변에 새 풀이 자란다(계획서 spread_seeds).
        풀 공급이 끊겨 초원이 사막화되는 것을 막는다. 전체 풀 수는 상한으로 제한."""
        # [←호출] update() 5단계(엔딩 중이 아닐 때).
        grasses = [p for p in self.plants if p.alive and p.name == "Grass"]
        if len(grasses) >= 85:                 # 상한: 너무 많으면 더 안 자람(과밀·물겹침 방지)
            return
        growth = self.environment.growth_multiplier()   # 날씨에 따른 성장 배율(비면 1.9 등)
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
                parent = random.choice(side)   # 기존 사이드 풀 하나를 부모로 골라 그 옆에 돋움
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
        """피식자/잡식이 안전·포만 상태이고 같은 종이 가까우면 낮은 확률로 번식.
        개체수가 줄어들수록 번식 확률이 완만하게 올라 멸종 직전 회복력을 높인다."""
        # [←호출] update() 5단계(엔딩 중이 아닐 때).
        # [변수] alive_by_name : 종별 현재 살아있는 마리 수(번식 상한 비교용).
        alive_by_name: dict[str, int] = {}
        for a in self.animals:
            if a.alive:
                alive_by_name[a.name] = alive_by_name.get(a.name, 0) + 1

        for animal in self.living_animals():
            if animal.hunger > 52 or animal.thirst > 52:   # 배고프거나 목마르면 번식 안 함
                continue
            if getattr(animal, "is_chased", False):        # 쫓기는 중이면 번식 안 함
                continue
            cap = 6 if animal.diet_type == "carnivore" else 12   # [변수] 종별 번식 상한
            cur = alive_by_name.get(animal.name, 1)              # [변수] 현재 마리 수
            if cur >= cap:
                continue
            # [변수] density_factor : 개체수가 적을수록 커지는 번식 확률 배율(최대 +1.5배).
            #        멸종 직전일수록 더 잘 태어나 회복력을 준다(이산 임계값 없는 연속 함수).
            density_factor = 1.0 + max(0.0, (cap * 0.5 - cur) / (cap * 0.5)) * 1.5
            mate_range = 80.0 if animal.diet_type != "carnivore" else 60.0
            mate = self.nearest_same_species(animal, mate_range)   # 가까운 같은 종(짝) 찾기
            if animal.diet_type == "carnivore":
                prob = 0.0010
            elif animal.name == "Elephant":
                prob = 0.0005   # 코끼리는 번식이 느리다 (일반 초식의 약 1/4)
            else:
                prob = 0.0018
            if mate is not None and random.random() < prob * density_factor:
                if animal.couple(animal, mate):     # [호출→] Animal.couple (성공 확률 1/2)
                    self.spawn_offspring(animal)     # 성공하면 새끼 예약

    def flush_pending(self):
        """이번 프레임에 태어난 새끼(_pending_animals)를 실제 animals 목록에 합친다."""
        # [←호출] update() 5단계 끝.
        # [이유] update 의 'for animal in self.animals' 루프 도중에 목록을 바꾸면 위험하므로,
        #        새끼는 임시 목록에 모아 뒀다가 루프가 끝난 지금 한 번에 합친다.
        if self._pending_animals:
            self.animals.extend(self._pending_animals)
            self._pending_animals = []

    def _elephant_bounce(self, living):
        """사자·하이에나가 코끼리에 닿으면 평면 상에서 이동 반대 방향으로 튕겨낸다."""
        # [←호출] update() 4단계.
        elephants = [a for a in living if a.name == "Elephant"]
        for elephant in elephants:
            for other in living:
                if other.name not in ("Lion", "Hyena"):
                    continue
                if elephant.position.distance_to(other.position) >= elephant.radius + other.radius + 4:
                    continue
                v = other.velocity
                if v.length_squared() > 4.0:
                    bounce_dir = -v.normalize()   # 이동 중이면 그 반대 방향으로
                else:
                    away = other.position - elephant.position
                    bounce_dir = away.normalize() if away.length_squared() > 1e-6 else Vector2(1, 0)
                power = other.speed * 1.4
                other.velocity = bounce_dir * power
                other.desired_velocity = bounce_dir * power

    def update_meerkat_ending(self, dt):
        """MEERKAT_ENDING_DAY 를 넘기면 미어캣들이 서서히 거대해지며(크기·체력·공격·속도)
        모든 동물·식물·나무를 잡아먹는다. 잠식이 진행되는 '연출'을 위해 점진적으로 성장한다."""
        # [←호출] update() 5단계.
        meerkats = [a for a in self.living_animals() if a.name == "Meerkat"]
        if not meerkats:
            return
        if self.environment.day < MEERKAT_ENDING_DAY:
            # 엔딩 전: 크기만 아주 조금씩 커진다(스탯·행동 변화 없음)
            for m in meerkats:
                m.draw_scale = min(1.4, m.draw_scale + dt * 0.006)
            return
        self.meerkat_ending = True   # 엔딩 시작! (이후 update 5단계의 번식·풀재생이 멈춘다)
        for m in meerkats:
            m.apocalypse = True   # 미어캣 behave 가 boss(잡아먹기) 모드로 바뀐다
            g = min(1.0, getattr(m, "_grow", 0.0) + dt * MEERKAT_GROW_PER_SEC)  # 0→1 서서히
            m._grow = g
            m.draw_scale = 1.4 + g * 3.1       # 화면 크기 최대 ~4.5배
            m.radius = 13.0 + g * 40.0         # 충돌 크기도 커짐
            m.power = 5.0 + g * 55.0           # 공격력 폭증
            m.speed = 82.0 + g * 60.0          # 속도↑
            m.detect_range = 130.0 + g * 550.0 # 탐지 범위↑
            m.max_health = 42.0 + g * 450.0
            m.health = m.max_health            # 잠식자는 무적에 가깝게 — 굶거나 지치지 않음
            m.hunger = m.thirst = 0.0
            m.stamina = 100.0

    def check_end_conditions(self):
        """종료 조건 검사: 미어캣 엔딩에서 다른 모든 것이 사라졌는가."""
        # [←호출] update() 5단계 끝.
        if self.meerkat_ending:
            others = [a for a in self.living_animals() if a.name != "Meerkat"]
            if not others and not self.alive_plants():
                self.environment.ended = True   # 시뮬레이션 종료 플래그(update 가 이후 멈춤)
                self.environment.end_reason = "미어캣이 초원의 모든 것을 집어삼켰습니다 - 미어캣 엔딩"

    # ── 생성/사망 ────────────────────────────────────────────────────────
    def spawn_carcass(self, animal):
        """동물이 죽은 자리에 사체를 만든다."""
        # [←호출] Animal.die() 안에서 'world.spawn_carcass(self)' 로 호출.
        self.resources.append(Carcass(Vector2(animal.position)))

    def spawn_offspring(self, parent):
        """부모 근처에 같은 종 새끼를 '예약'한다(_pending 에 넣었다가 flush_pending 에서 합침)."""
        # [←호출] try_reproduce() 에서 번식 성공 시.
        offset = Vector2(random.uniform(-30, 30), random.uniform(-30, 30))
        pos = self._clamp(parent.position + offset, 60)
        self._pending_animals.append(_ANIMAL_TYPES[parent.name](pos))

    # ── 컬렉션 질의 ──────────────────────────────────────────────────────
    def living_animals(self):
        """살아있는 동물만 추려 돌려준다(리스트 컴프리헨션)."""
        return [a for a in self.animals if a.alive]

    def alive_plants(self):
        return [p for p in self.plants if p.alive]

    def water_puddles(self):
        return [r for r in self.resources if isinstance(r, WaterPuddle) and r.alive]

    def carcasses(self):
        return [r for r in self.resources if isinstance(r, Carcass) and r.alive]

    def counts_by_name(self):
        """종(이름)별 살아있는 마리 수 딕셔너리(UI·headless 출력용)."""
        counts = {}
        for animal in self.living_animals():
            counts[animal.name] = counts.get(animal.name, 0) + 1
        return counts

    # ── nearest 질의 (행동 결정에 필요한 '사실' 제공) ────────────────────
    def _nearest(self, items, position, predicate=None, max_distance=None):
        """items 중 position 에 가장 가까운 (살아있고 조건을 만족하는) 것을 돌려준다.
        모든 nearest_* 질의가 이 한 함수 위에 만들어진다."""
        # [변수] best : 지금까지 찾은 최단 거리,  nearest : 그 대상.
        # [문법] float("inf") : 양의 무한대. '아직 아무것도 못 찾음'의 초기값으로 쓴다.
        best, nearest = float("inf"), None
        for item in items:
            if not item.alive:
                continue
            # [변수] predicate : '추가 조건' 함수(있으면). 예: '덤불인 것만', '주인 없는 사체만'.
            if predicate is not None and not predicate(item):
                continue
            d = position.distance_to(item.position)
            if max_distance is not None and d > max_distance:
                continue   # 탐지 범위 밖이면 무시
            if d < best:
                best, nearest = d, item
        return nearest

    def nearest_plant(self, position, max_distance=None):
        # [←호출] Herbivore/Omnivore.search_food 에서 먹이(풀) 찾을 때.
        return self._nearest(self.plants, position, max_distance=max_distance)

    def nearest_bush(self, position, max_distance):
        # [←호출] 포식자 매복(ambush)·초식 은신(behave) 에서 덤불 찾을 때.
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
        # [문법] lambda c: c.carried_by is None — 누가 옮기는 중이 아닌 사체만.
        return self._nearest(self.carcasses(), position,
                             lambda c: c.carried_by is None, max_distance)

    def nearest_water(self, position, max_distance=None):
        """물웅덩이 + 호숫가 중 가장 가까운 물."""
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
        """피식자 입장에서 보이는 포식자를 찾는다.
        - 덤불에 숨은(is_hidden) 포식자는 탐지 불가(기습 성립).
        - stealth 수치가 높을수록 더 가까이 와야 탐지된다(연속적 은신 효과).
          stealth=0.18 → 탐지 거리 89%, stealth=0.40 → 76%로 줄어든다."""
        # [←호출] Herbivore/Omnivore/Meerkat.behave 에서 위협 감지에 매 프레임 사용.
        best, nearest_pred = float("inf"), None
        for a in self.animals:
            if not a.alive:
                continue
            if a is animal or a.diet_type != "carnivore" or a.is_hidden:
                continue
            d = animal.position.distance_to(a.position)
            # stealth가 높을수록 먹이가 인식하는 유효 탐지 거리가 줄어든다
            stealth = getattr(a, 'stealth', 0.0)
            visible_range = max_distance * (1.0 - stealth * 0.55)
            if d > visible_range:
                continue
            if d < best:
                best, nearest_pred = d, a
        return nearest_pred

    def nearest_prey_for(self, predator, max_distance):
        """포식자의 사냥감(초식·잡식). 코끼리는 몸집이 커 제외(접근 시 stomp 로 쫓김)."""
        return self._nearest(self.animals, predator.position,
                             lambda a: a is not predator and a.name != "Elephant"
                                       and a.diet_type in ("herbivore", "omnivore"),
                             max_distance)

    def nearest_named(self, name, position, max_distance):
        """특정 이름의 동물 중 가장 가까운 것(예: 사자가 'Elephant' 회피할 때)."""
        return self._nearest(self.animals, position,
                             lambda a: a.name == name, max_distance)

    def nearest_same_species(self, animal, radius):
        """같은 종 짝(번식용). 자기 자신은 제외."""
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
        """특정 지형(예: 'Cave')에서 가장 가까운 것(미어캣·혹멧돼지가 굴 찾을 때)."""
        return self._nearest(self.terrains, position,
                             lambda t: t.name == terrain_name)
