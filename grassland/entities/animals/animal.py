# =============================================================================
# entities/animals/animal.py — 모든 동물의 공통 부모 (계획서 Animal)
# 계획서에 명시된 공통 속성/메서드만 둔다. 종별 행동은 자식이 오버라이드.
#
# [움직임 철학]
#   평소(상호작용 없음)  : wander() — '상관 랜덤워크'. 진행 방향(heading)을 매
#                          프레임 아주 조금씩만 틀어 부드럽게 휘어 다닌다.
#   상호작용 발생(추격·도주·먹이·물) : move_toward/away 로 '특정 방향' 지향.
#   어느 쪽이든 desired_velocity 만 적고, 실제 가감속·회전은 physics 가 부드럽게.
# =============================================================================
#
#  [실행 흐름에서의 위치 — 동물 AI 의 뼈대]
#    매 프레임 world.update() 3단계에서 animal.update(world, dt) 가 호출된다.
#    그 흐름은 항상:  update() → behave() (할 일을 찾음) → 못 찾으면 wander()(어슬렁).
#    behave() 는 여기선 '결정 없음(False)'이고, 식성별 자식(Carnivore/Herbivore/Omnivore)과
#    종별 클래스(Lion 등)가 오버라이드해 진짜 판단을 한다.
#    → 즉 '한 동물이 매 순간 무엇을 하는가'의 출발점이 이 파일의 update() 다.
# =============================================================================
import math
import random

from pygame.math import Vector2

# [흐름 0] Animal 은 Entity 를 상속한다 → 좌표·이동의도(move_toward 등)를 그대로 물려받는다.
from grassland.entities.entity import Entity


class Animal(Entity):
    # [문법] 클래스 변수(상수) : 모든 동물이 공유하는 기준값.
    HUNGER_SEARCH_LEVEL = 80.0     # [변수] 이 허기 이상이면 '배고픔'으로 보고 먹이 탐색을 우선
    ENERGY_COST_MULTIPLIER = 0.6   # [변수] 기력 소모량에 곱하는 배율(전체 소모 강도 조절 손잡이)

    def __init__(self, name, position, color, health, speed, power,
                 detect_range, radius=18):
        # [←호출] 식성별 부모(Carnivore 등)의 __init__ 이 super().__init__(...) 으로 호출.
        # [흐름] Entity.__init__ 을 먼저 불러 좌표·표시 데이터를 세팅(kind="animal", layer=3).
        super().__init__(name=name, position=position, radius=radius,
                         color=color, kind="animal", layer=3)
        # ── 계획서 공통 속성 ─────────────────────────────────────────
        self.health = health             # [변수] 현재 체력
        self.max_health = health         # [변수] 최대 체력(체력바 비율 계산에 사용)
        self.speed = speed               # [변수] 기본 속도(아래 @property 로 기력 보정됨)
        self.power = power               # [변수] 공격력(attack 시 상대 체력을 깎는 양)
        self.hunger = random.uniform(12.0, 42.0)   # [변수] 허기 0~100(개체마다 다르게 시작)
        self.thirst = random.uniform(12.0, 42.0)   # [변수] 갈증 0~100
        self.is_sleeping = False         # [변수] 수면 상태(현재 거의 미사용)
        self.stamina = 100.0             # [변수] 기력 0~100(이동·전투로 소모, 낮으면 느려짐)
        self.stamina_recovery_rate = 0.05  # [변수] 가만히 있을 때 초당 기력 회복량(매우 느림)
        self.stress = 0.0                # [변수] 스트레스 0~100(쫓기면 증가, 경계심·회복에 영향)
        self.detect_range = detect_range # [변수] 위협/사냥 탐지 거리
        # 먹이(풀·사체) 탐지 거리 — 위협/사냥용 detect_range 와 분리해 종별로 다르게 둔다.
        # 짧을수록 멀리 있는 먹이엔 안 몰린다(사체 하나에 떼로 쏠리는 문제 방지).
        self.food_range = detect_range * 0.7   # [변수] 먹이 탐지 거리
        self.thirst_limit = 75.0     # [변수] 이 갈증을 넘으면 물을 찾아 나선다(종별로 다르게 설정)
        self.is_hidden = False       # [변수] 은신 중인가(덤불·동굴). 매 프레임 world 가 False로 초기화
        self.age = 0.0               # [변수] 살아온 시간(초)
        self.diet_type = ""          # [변수] 식성 — 자식이 herbivore/carnivore/omnivore 로 설정
        self._carcass_spawned = False  # [변수] 죽을 때 사체를 이미 만들었는지(중복 방지)
        # ── 전투 쿨다운: 공격이 매 프레임 들어가 즉사하는 것을 막는다 ──────
        self.attack_timer = 0.0      # [변수] 다음 타격까지 남은 시간(0 이하일 때만 실제 타격)
        self.attack_cooldown = 0.7   # [변수] 한 번 때린 뒤 다음 타격까지(초)
        # ── 섭취 쿨다운: 한 입에 조금씩만, 쿨타임마다 한 번 ──────────────
        self.feed_timer = 0.0        # [변수] 다음 한 입까지 남은 시간
        self.feed_cooldown = 0.55    # [변수] 한 입 먹고/마시고 다음까지(초)
        # ── 랜덤워크 상태(wander 가 사용) ─────────────────────────────
        self.heading = random.uniform(0.0, 360.0)     # [변수] 현재 진행 방향(도)
        self.wander_timer = random.uniform(0.4, 2.0)   # [변수] 다음 '쉼/이동' 전환까지 남은 시간
        self.is_resting = False                        # [변수] 잠깐 멈춰 주변을 살피는 중인가
        self._cruise = speed * 0.35                    # [변수] 어슬렁 순항 속도(세그먼트마다 갱신)
        self._roam = None                              # [변수] 가끔 잡는 '맵 먼 곳' 목적지(없으면 None)
        self._roam_chance = 0.4                        # [변수] 세그먼트마다 먼 곳 로밍을 새로 잡을 확률
        self._juke_sign = random.choice((-1, 1))       # [변수] 지그재그 회피의 현재 좌/우(+1/-1)
        self._juke_timer = random.uniform(0.3, 0.6)    # [변수] 다음 좌우 전환까지(초)
        self._turn_rate = random.uniform(-60.0, 60.0)  # [변수] 어슬렁 각속도(도/초) — 부드러운 곡선 경로
        self.interaction_target = None                 # [변수] 이번 프레임 상호작용 대상(먹이·물·적)
        self._committed_food = None                    # [변수] 한 번 정한 먹이 대상(자꾸 바꾸지 않게 고정)

    @property
    def speed(self):
        """스태미나 기반 속도 — 기력이 떨어질수록 느려진다(S커브)."""
        # [문법] @property : speed 를 '메서드'로 정의하되 'self.speed'처럼 '변수처럼' 읽게 해 준다.
        #        읽을 때마다 아래 계산이 돌아 항상 현재 기력을 반영한 속도가 나온다.
        t = self.stamina / 100.0                       # 기력 비율 0~1
        return self._base_speed * (0.3 + 0.7 * t ** 0.5)  # 기력 100→1배, 0→0.3배 (제곱근으로 완만)

    @speed.setter
    def speed(self, value):
        """self.speed = X 로 '쓸' 때는 실제로 _base_speed 에 저장한다."""
        # [문법] @속성.setter : 위 property 에 '쓰기' 동작을 붙인다. 읽기/쓰기를 분리해
        #        '쓰면 기본값 저장, 읽으면 기력 보정값 반환'을 가능하게 한다.
        self._base_speed = value

    # ── 계획서 공통 메서드 ───────────────────────────────────────────
    def _feed_ready(self):
        """섭취 쿨다운 — 준비됐으면 True 로 만들고 타이머를 건다(한 입씩만 먹게)."""
        if self.feed_timer > 0.0:
            return False                       # 아직 쿨타임 → 이번엔 안 먹음
        self.feed_timer = self.feed_cooldown   # 쿨타임 새로 걸고
        return True                            # 이번 한 입은 허용

    def eat(self, food):
        """food 는 consume(amount) 또는 reduce_hunger(self) 를 가진 객체(덕 타이핑).
        쿨다운마다 '한 입'만 조금씩 먹는다."""
        # [←호출] 자식의 search_food 가 먹이에 닿았을 때.
        self.interaction_target = food
        self.action_text = "eat"
        if not self._feed_ready():
            return
        # [문법] hasattr(food, "이름") : food 에 그 메서드가 있는지 보고 알맞게 호출(덕 타이핑).
        if hasattr(food, "reduce_hunger"):        # 사체 등(reduce_hunger 를 가진 것)
            food.reduce_hunger(self)
        elif hasattr(food, "consume"):            # 식물 등(consume 을 가진 것)
            eaten = food.consume(10)              # 10만큼 먹으려 시도 → 실제 먹은 양 반환
            self.hunger = max(0.0, self.hunger - eaten)   # 먹은 만큼 허기 감소
        self.stamina = min(100.0, self.stamina + 7.5)     # 먹으면 기력 약간 회복

    def drink(self, source):
        """source 는 reduce_thirst(self) 또는 enable_drinking(self) 를 가진 객체.
        쿨다운마다 '한 모금'만 조금씩 마신다."""
        # [←호출] seek_water_if_needed 가 물에 닿았을 때.
        self.interaction_target = source
        self.action_text = "drink"
        if not self._feed_ready():
            return
        if hasattr(source, "reduce_thirst"):
            source.reduce_thirst(self)
        elif hasattr(source, "enable_drinking"):
            source.enable_drinking(self)
        self.stamina = min(100.0, self.stamina + 2.5)

    def sleep(self):
        self.is_sleeping = True
        self.action_text = "sleep"

    def wake_up(self):
        self.is_sleeping = False

    def lose_energy(self, amount):
        """기력을 amount 만큼 소모(ENERGY_COST_MULTIPLIER 배율 적용, 0 미만 방지)."""
        self.stamina = max(0.0, self.stamina - amount * self.ENERGY_COST_MULTIPLIER)

    def die(self, world=None):
        """죽음 처리: 정지 + 사체 생성(중복 방지)."""
        # [←호출] attack() 에서 상대 체력이 0 이하가 됐을 때, 또는 코끼리 stomp 등.
        if not self.alive:
            return                             # 이미 죽었으면 아무것도 안 함
        self.alive = False
        self.velocity = Vector2()          # 죽으면 즉시 정지
        self.desired_velocity = Vector2()
        self.action_text = "dead"
        if world is not None and not self._carcass_spawned:
            self._carcass_spawned = True
            world.spawn_carcass(self)        # [호출→] World.spawn_carcass(죽은 자리에 사체)

    def status(self):
        # [문법] super().status() : 부모(Entity)의 같은 메서드를 그대로 호출.
        return super().status()

    def distant_to(self, target):            # 계획서 표기(distant_to) 유지
        return self.distance_to(target)

    def attack(self, target, world):
        """공격. 단, 쿨다운 중이면 '겨누는' 모션만 하고 실제 타격은 안 들어간다.
        (매 프레임 데미지가 들어가 즉사하던 문제를 막는다 — 초당 ~1.4회만 타격)"""
        # [←호출] 사냥(hunt)·반격(fight_or_flight)·코끼리 stomp 등 곳곳에서.
        if not target.alive:
            return
        self.interaction_target = target
        self.action_text = "attack"
        if self.attack_timer > 0.0:
            return                             # 쿨타임 중 → 겨누기만(데미지 없음)
        self.attack_timer = self.attack_cooldown
        # 날씨에 따른 전투력 보정(무더위엔 약하게) — world 가 있으면 적용
        factor = world.environment.combat_factor() if world is not None else 1.0
        target.health -= self.power * factor   # 실제 데미지
        target.stress = min(100.0, target.stress + 8.0)
        if target.health <= 0:
            target.die(world)                  # [호출→] 상대 die(체력 0 이하면 사망)

    def tick_combat(self, dt):
        """전투 쿨다운 감소 — 매 update 에서 호출."""
        if self.attack_timer > 0.0:
            self.attack_timer = max(0.0, self.attack_timer - dt)

    def couple(self, one, other):
        """번식 성공 여부(확률 1/2). World 가 호출해 새 개체를 만든다."""
        # [←호출] World.try_reproduce 에서.
        if one.alive and other.alive:
            # [문법] round(uniform(0,1)) → 0 또는 1, bool(...) → False/True (즉 50% 확률)
            return bool(round(random.uniform(0, 1)))
        return False

    def recover_stamina(self, dt):
        """패시브 기력 회복(아주 느림) + 이동 소모 + 각종 타이머 감소."""
        # [←호출] update() 매 프레임 첫머리.
        self.stamina = min(100.0, self.stamina + self.stamina_recovery_rate * dt)
        if self.velocity.length_squared() > 1.0:   # 움직이는 중이면 기력 소모
            self.lose_energy(0.25 * dt)
        if self.feed_timer > 0.0:                   # 섭취 쿨다운 감소
            self.feed_timer = max(0.0, self.feed_timer - dt)
        self.tick_combat(dt)                        # 전투 쿨다운 감소

    def hunger_speed_factor(self):
        """심하게 배고플수록 최고 속도가 줄어든다. 80 전까지는 정상, 100에서 65%."""
        # [←호출] physics._desired 가 속도 상한 계산에 사용.
        if self.hunger < self.HUNGER_SEARCH_LEVEL:
            return 1.0
        pressure = min(1.0, (self.hunger - self.HUNGER_SEARCH_LEVEL) / 20.0)
        return 1.0 - 0.35 * pressure

    # ── 공통 행동 보조(여러 종이 공유) ───────────────────────────────
    def seek_water_if_needed(self, world):
        """목이 마르면(종별 thirst_limit 초과) '탐지범위 안'의 물로 이동·음수. 행동했으면 True.
        물이 탐지 범위 밖이면 안 보이는 것으로 보고 False(→ 랜덤워크하다 가까워지면 탐지).
        단, 아주 목마르면(>92) 범위를 무시하고 물을 찾아 나선다(탈수 방지)."""
        # [←호출] 각 식성 behave() 의 '물 찾기' 단계.
        limit = min(self.thirst_limit, 25.0) if self.stamina < 25.0 else self.thirst_limit
        if self.thirst < limit:
            return False                       # 아직 안 목마름 → 다른 행동에 양보
        reach = None if self.thirst > 92.0 else self.detect_range   # 아주 목마르면 거리 무제한
        water = world.nearest_water(self.position, reach)   # [호출→] World.nearest_water
        if water is None:
            return False
        self.interaction_target = water
        if self.distance_to(water) <= self.radius + water.radius + 8:
            self.drink(water)                  # 닿았으면 마시고
            self.stop()
        else:
            self.move_toward(water.position, self.speed * 0.85)   # 멀면 물 쪽으로 이동
            self.action_text = "water"
        return True

    def _food_valid(self, food):
        """committed 먹이 대상이 아직 유효한지 확인(죽었거나 다 먹혔으면 False)."""
        if food is None:
            return False
        # 살아있는 먹잇감(prey) — diet_type 속성으로 '동물'임을 판별
        if hasattr(food, 'diet_type'):
            return food.alive and self.distance_to(food) <= self.detect_range * 1.5
        # 사체 — amount 속성으로 판별
        if hasattr(food, 'amount'):
            return (getattr(food, 'alive', True) and food.amount > 0
                    and food.id not in getattr(self, '_finished_carcasses', set()))
        # 식물/나무
        return getattr(food, 'alive', False) and getattr(food, 'health', 1) > 0

    def search_food(self, world, dt):
        """먹이 탐색 — 빈 구현. 각 서브클래스(Herbivore/Carnivore/Omnivore)가 오버라이드."""
        return False

    def evade(self, threat_pos, speed, dt, lateral=0.7, period=0.45):
        """지그재그 회피 — 포식자 반대 방향 + 좌우로 '번갈아' 꺾는 횡방향 성분을 더한다.
        포식자는 steering 관성(agility)으로 급커브를 못 따라와 컷마다 살짝 헛돈다(추격 회피).
        juke 부호가 개체마다 달라, 무리가 한 방향으로 쏠리지 않고 사방으로 흩어진다."""
        # [←호출] Herbivore.fight_or_flight, Gazelle.zigzag, Omnivore.flee_or_fight 등.
        away = self.position - threat_pos                  # 위협에서 멀어지는 방향
        away = away.normalize() if away.length_squared() > 1e-9 \
            else Vector2(1.0, 0.0).rotate(random.uniform(0, 360))   # 겹쳐 있으면 임의 방향
        self._juke_timer -= dt
        if self._juke_timer <= 0.0:
            self._juke_sign = -self._juke_sign             # 좌/우 전환
            self._juke_timer = random.uniform(period * 0.7, period * 1.3)
        # [변수] perp : away 에 수직인 방향(좌우). (x,y)→(-y,x) 가 90도 회전이다.
        perp = Vector2(-away.y, away.x) * (self._juke_sign * lateral)
        self.desired_velocity = (away + perp).normalize() * speed   # 뒤+옆 = 지그재그
        self.action_text = "flee"
        self.lose_energy(5.0 * dt)

    def wander(self, world, dt):
        """할 일이 없을 때 — 부드러운 어슬렁 + 가끔 '맵 먼 곳 로밍'으로 전체 맵을 누빈다
        (한쪽으로 쏠리지 않게). heading 을 매 프레임 작은 각도만 흔들어 완만한 곡선을 만든다."""
        # [←호출] update() 에서 behave() 가 False(할 일 없음)를 줄 때.
        # 1) 가끔 '쉼 ↔ 이동' 을 바꾸고, 순항 속도를 한 번만 새로 정한다(세그먼트 동안 일정).
        #    또 가끔 맵의 먼 지점을 목적지로 잡아 멀리까지 돌아다니게 한다.
        self.wander_timer -= dt
        if self.wander_timer <= 0.0:
            hungry = self.hunger >= self.HUNGER_SEARCH_LEVEL   # 배고프면 더 부지런히 돌아다님
            self.is_resting = False if hungry else random.random() < 0.12
            self.wander_timer = random.uniform(0.35, 0.9) if hungry else random.uniform(0.8, 2.2)
            lo, hi = (0.48, 0.62) if hungry else (0.30, 0.42)
            self._cruise = self.speed * random.uniform(lo, hi)
            roam_chance = 0.95 if hungry else self._roam_chance
            if self._roam is None and random.random() < roam_chance:
                if world.environment.weather == "drought":
                    # 가뭄이면 '잎 무성한 나무'(그늘)를 목적지로 → 더위를 피해 모임
                    tree = world.nearest_tree(self.position, need_foliage=True)
                    self._roam = tree.position.copy() if tree is not None else \
                        Vector2(random.uniform(0, world.width), random.uniform(0, world.height))
                else:
                    self._roam = Vector2(random.uniform(0, world.width),
                                         random.uniform(0, world.height))

        if self.is_resting:
            self.stop()
            self.action_text = "wander"
            return

        # 2) 로밍 목적지가 있으면 그쪽으로 이동. 완전한 직선이 아닌 사인파 흔들림을 섞어
        #    자연스럽게 구불구불 이동하도록 한다. 도착하면 해제.
        if self._roam is not None:
            to = self._roam - self.position
            if to.length() < 60.0:
                self._roam = None                          # 거의 도착 → 목적지 해제
            else:
                self.heading = Vector2(1.0, 0.0).angle_to(to)
                perp = Vector2(-to.y, to.x).normalize()
                # [문법] math.sin(self.age * ...) : 시간에 따라 좌우로 흔들리는 사인파(구불구불 효과)
                wobble = perp * math.sin(self.age * 1.3) * 0.28
                self.desired_velocity = (to.normalize() + wobble).normalize() * (self.speed * 0.5)
                self.action_text = "wander"
                return

        # 3) 각속도(_turn_rate)를 부드럽게 변화시켜 자연스러운 곡선 경로를 만든다.
        #    매 프레임 독립 랜덤값을 더하는 대신, 각속도에 랜덤 가속을 주고 지수 감쇠시킨다.
        #    → 한동안 같은 방향으로 휘다가 서서히 방향을 바꾸는 유기적인 움직임이 나온다.
        self._turn_rate += random.uniform(-220.0, 220.0) * dt
        self._turn_rate *= math.exp(-2.0 * dt)          # 감쇠: 1 초 후 약 13 % 남음
        self._turn_rate = max(-130.0, min(130.0, self._turn_rate))   # 각속도 상·하한
        self.heading += self._turn_rate * dt            # 방향을 조금씩 틀기
        self.desired_velocity = Vector2(1.0, 0.0).rotate(self.heading) * self._cruise
        self.action_text = "wander"

    # ── 매 틱 갱신(자식이 오버라이드) ────────────────────────────────
    def update(self, world, dt):
        """동물 한 마리의 매 프레임 진입점. (식성별 자식이 hunger/thirst 증가를 더해 오버라이드)"""
        # [←호출] world.update() 3단계: 'for animal in self.animals: animal.update(self, dt)'.
        if not self.alive:
            return
        self.age += dt
        self.recover_stamina(dt)              # 기력 회복 + 타이머 감소
        # [흐름] behave 가 '할 일을 찾으면' True → 끝. 못 찾으면(False) wander(어슬렁).
        if not self.behave(world, dt):        # [호출→] 종별 behave()
            self.wander(world, dt)            # [호출→] wander()

    def behave(self, world, dt):
        """무엇을 할지 결정. 기본은 '결정 없음'(False). 종별로 오버라이드."""
        # [문법] 이 메서드를 자식(Carnivore/Herbivore/Omnivore/Lion...)이 다시 정의(오버라이드)해
        #        실제 판단(사냥·도주·먹이찾기)을 넣는다. 여기 기본형은 항상 False(→ wander).
        return False
