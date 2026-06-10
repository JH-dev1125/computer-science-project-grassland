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
import random

from pygame.math import Vector2

from grassland.entities.entity import Entity


class Animal(Entity):
    def __init__(self, name, position, color, health, speed, power,
                 detect_range, radius=18):
        super().__init__(name=name, position=position, radius=radius,
                         color=color, kind="animal", layer=3)
        # ── 계획서 공통 속성 ─────────────────────────────────────────
        self.health = health
        self.max_health = health
        self.speed = speed
        self.power = power
        self.hunger = random.uniform(12.0, 42.0)
        self.thirst = random.uniform(12.0, 42.0)
        self.is_sleeping = False
        self.stamina = 100.0
        self.stamina_recovery_rate = 7.0
        self.stamina_drain = 30.0    # 전력질주 시 초당 기력 소모(달리는 속도에 비례)
        self.stress = 0.0
        self.detect_range = detect_range
        # 먹이(풀·사체) 탐지 거리 — 위협/사냥용 detect_range 와 분리해 종별로 다르게 둔다.
        # 짧을수록 멀리 있는 먹이엔 안 몰린다(사체 하나에 떼로 쏠리는 문제 방지).
        self.food_range = detect_range * 0.7
        self.thirst_limit = 75.0     # 이 갈증을 넘으면 물을 찾아 나선다(종별로 다르게 설정)
        self.is_hidden = False
        self.age = 0.0
        self.diet_type = ""          # 자식이 herbivore/carnivore/omnivore 로 설정
        self._carcass_spawned = False
        # ── 전투 쿨다운: 공격이 매 프레임 들어가 즉사하는 것을 막는다 ──────
        self.attack_timer = 0.0      # 0 이하일 때만 실제 타격이 들어간다
        self.attack_cooldown = 0.7   # 한 번 때린 뒤 다음 타격까지(초)
        # ── 섭취 쿨다운: 한 입에 조금씩만, 쿨타임마다 한 번 ──────────────
        self.feed_timer = 0.0
        self.feed_cooldown = 0.55    # 한 입 먹고/마시고 다음까지(초)
        # ── 랜덤워크 상태 ────────────────────────────────────────────
        self.heading = random.uniform(0.0, 360.0)     # 현재 진행 방향(도)
        self.wander_timer = random.uniform(0.4, 2.0)   # 다음 '쉼/이동' 전환까지
        self.is_resting = False                        # 잠깐 멈춰 주변을 살피는 중
        self._cruise = speed * 0.35                    # 어슬렁 순항 속도(세그먼트마다 갱신)
        self._roam = None                              # 가끔 잡는 '맵 먼 곳' 목적지(전체 맵 사용)
        self._roam_chance = 0.4                         # 세그먼트마다 먼 곳 로밍을 새로 잡을 확률
        self._juke_sign = random.choice((-1, 1))       # 지그재그 회피의 현재 좌/우
        self._juke_timer = random.uniform(0.3, 0.6)    # 다음 좌우 전환까지(초)
        self.interaction_target = None                 # 이번 프레임 상호작용 대상

    # ── 계획서 공통 메서드 ───────────────────────────────────────────
    def _feed_ready(self):
        """섭취 쿨다운 — 준비됐으면 True 로 만들고 타이머를 건다(한 입씩만 먹게)."""
        if self.feed_timer > 0.0:
            return False
        self.feed_timer = self.feed_cooldown
        return True

    def eat(self, food):
        """food 는 consume(amount) 또는 reduce_hunger(self) 를 가진 객체(덕 타이핑).
        쿨다운마다 '한 입'만 조금씩 먹는다."""
        self.interaction_target = food
        self.action_text = "eat"
        if not self._feed_ready():
            return
        if hasattr(food, "reduce_hunger"):        # 사체 등
            food.reduce_hunger(self)
        elif hasattr(food, "consume"):            # 식물 등
            eaten = food.consume(10)
            self.hunger = max(0.0, self.hunger - eaten)

    def drink(self, source):
        """source 는 reduce_thirst(self) 또는 enable_drinking(self) 를 가진 객체.
        쿨다운마다 '한 모금'만 조금씩 마신다."""
        self.interaction_target = source
        self.action_text = "drink"
        if not self._feed_ready():
            return
        if hasattr(source, "reduce_thirst"):
            source.reduce_thirst(self)
        elif hasattr(source, "enable_drinking"):
            source.enable_drinking(self)

    def sleep(self):
        self.is_sleeping = True
        self.action_text = "sleep"

    def wake_up(self):
        self.is_sleeping = False

    def lose_energy(self, amount):
        self.stamina = max(0.0, self.stamina - amount)

    def die(self, world=None):
        if not self.alive:
            return
        self.alive = False
        self.velocity = Vector2()          # 죽으면 즉시 정지
        self.desired_velocity = Vector2()
        self.action_text = "dead"
        if world is not None and not self._carcass_spawned:
            self._carcass_spawned = True
            world.spawn_carcass(self)        # 죽으면 사체 생성

    def status(self):
        return super().status()

    def distant_to(self, target):            # 계획서 표기(distant_to) 유지
        return self.distance_to(target)

    def attack(self, target, world):
        """공격. 단, 쿨다운 중이면 '겨누는' 모션만 하고 실제 타격은 안 들어간다.
        (매 프레임 데미지가 들어가 즉사하던 문제를 막는다 — 초당 ~1.4회만 타격)"""
        if not target.alive:
            return
        self.interaction_target = target
        self.action_text = "attack"
        if self.attack_timer > 0.0:
            return
        self.attack_timer = self.attack_cooldown
        # 날씨에 따른 전투력 보정(무더위엔 약하게) — world 가 있으면 적용
        factor = world.environment.combat_factor() if world is not None else 1.0
        target.health -= self.power * factor
        target.stress = min(100.0, target.stress + 8.0)
        if target.health <= 0:
            target.die(world)

    def tick_combat(self, dt):
        """전투 쿨다운 감소 — 매 update 에서 호출."""
        if self.attack_timer > 0.0:
            self.attack_timer = max(0.0, self.attack_timer - dt)

    def couple(self, one, other):
        """번식 성공 여부(확률 1/2). World 가 호출해 새 개체를 만든다."""
        if one.alive and other.alive:
            return bool(round(random.uniform(0, 1)))
        return False

    def recover_stamina(self, dt):
        """실제 이동 속도에 따라 기력을 소모/회복한다(매 update 호출).
        빠르게 달리면(>0.6×speed) 지치고, 느리거나 멈추면 회복한다.
        기력이 낮으면 physics 가 최고 속도를 깎아 '지쳐서 느려지는' 효과를 준다."""
        run = self.velocity.length() / max(self.speed, 1.0)
        if run > 0.6:
            self.stamina = max(0.0, self.stamina - (run - 0.6) * self.stamina_drain * dt)
        else:
            self.stamina = min(100.0, self.stamina + self.stamina_recovery_rate * dt)
        if self.feed_timer > 0.0:
            self.feed_timer = max(0.0, self.feed_timer - dt)
        self.tick_combat(dt)   # 모든 동물이 매 update 에서 호출 → 전투 쿨다운 감소

    # ── 공통 행동 보조(여러 종이 공유) ───────────────────────────────
    def seek_water_if_needed(self, world):
        """목이 마르면(종별 thirst_limit 초과) '탐지범위 안'의 물로 이동·음수. 행동했으면 True.
        물이 탐지 범위 밖이면 안 보이는 것으로 보고 False(→ 랜덤워크하다 가까워지면 탐지).
        단, 아주 목마르면(>92) 범위를 무시하고 물을 찾아 나선다(탈수 방지)."""
        if self.thirst < self.thirst_limit:
            return False
        reach = None if self.thirst > 92.0 else self.detect_range
        water = world.nearest_water(self.position, reach)
        if water is None:
            return False
        self.interaction_target = water
        if self.distance_to(water) <= self.radius + water.radius + 8:
            self.drink(water)
            self.stop()
        else:
            self.move_toward(water.position, self.speed * 0.85)
            self.action_text = "water"
        return True

    def seek_plants_if_needed(self, world):
        """배고프면 가장 가까운 식물로 이동·섭취. 행동했으면 True."""
        if self.hunger < 35.0:
            return False
        reach = None if self.hunger > 92.0 else self.food_range
        plant = world.nearest_plant(self.position, reach)
        if plant is None:
            return False
        self.interaction_target = plant
        if self.distance_to(plant) <= self.radius + plant.radius + 8:
            self.eat(plant)
            self.stop()
        else:
            self.move_toward(plant.position, self.speed * 0.7)
            self.action_text = "graze"
        return True

    def evade(self, threat_pos, speed, dt, lateral=0.7, period=0.45):
        """지그재그 회피 — 포식자 반대 방향 + 좌우로 '번갈아' 꺾는 횡방향 성분을 더한다.
        포식자는 steering 관성(agility)으로 급커브를 못 따라와 컷마다 살짝 헛돈다(추격 회피).
        juke 부호가 개체마다 달라, 무리가 한 방향으로 쏠리지 않고 사방으로 흩어진다."""
        away = self.position - threat_pos
        away = away.normalize() if away.length_squared() > 1e-9 \
            else Vector2(1.0, 0.0).rotate(random.uniform(0, 360))
        self._juke_timer -= dt
        if self._juke_timer <= 0.0:
            self._juke_sign = -self._juke_sign
            self._juke_timer = random.uniform(period * 0.7, period * 1.3)
        perp = Vector2(-away.y, away.x) * (self._juke_sign * lateral)
        self.desired_velocity = (away + perp).normalize() * speed
        self.action_text = "flee"

    def wander(self, world, dt):
        """할 일이 없을 때 — 부드러운 어슬렁 + 가끔 '맵 먼 곳 로밍'으로 전체 맵을 누빈다
        (한쪽으로 쏠리지 않게). heading 을 매 프레임 작은 각도만 흔들어 완만한 곡선을 만든다."""
        # 1) 가끔 '쉼 ↔ 이동' 을 바꾸고, 순항 속도를 한 번만 새로 정한다(세그먼트 동안 일정).
        #    또 가끔 맵의 먼 지점을 목적지로 잡아 멀리까지 돌아다니게 한다.
        self.wander_timer -= dt
        if self.wander_timer <= 0.0:
            self.is_resting = random.random() < 0.12
            self.wander_timer = random.uniform(0.8, 2.2)
            self._cruise = self.speed * random.uniform(0.30, 0.42)
            if self._roam is None and random.random() < self._roam_chance:
                if world.environment.weather == "drought":
                    tree = world.nearest_tree(self.position, need_foliage=True)
                    self._roam = tree.position.copy() if tree is not None else \
                        Vector2(random.uniform(0, world.width), random.uniform(0, world.height))
                else:
                    self._roam = Vector2(random.uniform(0, world.width),
                                         random.uniform(0, world.height))

        if self.is_resting:
            self.stop()
            self.action_text = "watch"
            return

        # 2) 로밍 목적지가 있으면 그쪽으로 또박또박 이동(맵 전체 사용). 도착하면 해제.
        if self._roam is not None:
            to = self._roam - self.position
            if to.length() < 60.0:
                self._roam = None
            else:
                self.heading = Vector2(1.0, 0.0).angle_to(to)   # 로밍 끝나면 그 방향서 이어감
                self.desired_velocity = to.normalize() * (self.speed * 0.5)
                self.action_text = "roam"
                return

        # 3) 평소엔 heading 을 조금씩만 회전(부드러운 곡선).
        self.heading += random.uniform(-45.0, 45.0) * dt
        self.desired_velocity = Vector2(1.0, 0.0).rotate(self.heading) * self._cruise
        self.action_text = "wander"

    # ── 매 틱 갱신(자식이 오버라이드) ────────────────────────────────
    def update(self, world, dt):
        if not self.alive:
            return
        self.age += dt
        self.recover_stamina(dt)
        if not self.behave(world, dt):
            self.wander(world, dt)

    def behave(self, world, dt):
        """무엇을 할지 결정. 기본은 '결정 없음'(False). 종별로 오버라이드."""
        return False
