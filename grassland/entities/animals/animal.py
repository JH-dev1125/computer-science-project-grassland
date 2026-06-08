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

from grassland.entities.base import Entity


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
        self.stress = 0.0
        self.detect_range = detect_range
        self.is_hidden = False
        self.age = 0.0
        self.diet_type = ""          # 자식이 herbivore/carnivore/omnivore 로 설정
        self._carcass_spawned = False
        # ── 전투 쿨다운: 공격이 매 프레임 들어가 즉사하는 것을 막는다 ──────
        self.attack_timer = 0.0      # 0 이하일 때만 실제 타격이 들어간다
        self.attack_cooldown = 0.7   # 한 번 때린 뒤 다음 타격까지(초)
        # ── 랜덤워크 상태 ────────────────────────────────────────────
        self.heading = random.uniform(0.0, 360.0)     # 현재 진행 방향(도)
        self.wander_timer = random.uniform(0.4, 2.0)   # 다음 '쉼/이동' 전환까지
        self.is_resting = False                        # 잠깐 멈춰 주변을 살피는 중
        self.interaction_target = None                 # 이번 프레임 상호작용 대상

    # ── 계획서 공통 메서드 ───────────────────────────────────────────
    def eat(self, food):
        """food 는 consume(amount) 또는 reduce_hunger(self) 를 가진 객체(덕 타이핑)."""
        self.interaction_target = food
        if hasattr(food, "reduce_hunger"):        # 사체 등
            food.reduce_hunger(self)
        elif hasattr(food, "consume"):            # 식물 등
            eaten = food.consume(40)
            self.hunger = max(0.0, self.hunger - eaten)
        self.action_text = "eat"

    def drink(self, source):
        """source 는 reduce_thirst(self) 또는 enable_drinking(self) 를 가진 객체."""
        self.interaction_target = source
        if hasattr(source, "reduce_thirst"):
            source.reduce_thirst(self)
        elif hasattr(source, "enable_drinking"):
            source.enable_drinking(self)
        self.action_text = "drink"

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
        target.health -= self.power
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
        self.stamina = min(100.0, self.stamina + self.stamina_recovery_rate * dt)
        self.tick_combat(dt)   # 모든 동물이 매 update 에서 호출 → 전투 쿨다운 감소

    # ── 공통 행동 보조(여러 종이 공유) ───────────────────────────────
    def seek_water_if_needed(self, world):
        """목이 마르면 가장 가까운 물로 이동·음수. 행동했으면 True."""
        if self.thirst < 58.0:
            return False
        water = world.nearest_water(self.position)
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
        plant = world.nearest_plant(self.position)
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

    def wander(self, dt):
        """할 일이 없을 때 — '상관 랜덤워크'로 부드럽게 어슬렁.
        진행 방향(heading)을 매 프레임 작은 각도만 흔들어, 직선+급회전이 아니라
        완만하게 휘어지는 경로를 만든다. 가끔 잠깐 멈춰 주변을 살핀다."""
        # 1) 가끔 '쉼 ↔ 이동' 상태를 바꾼다
        self.wander_timer -= dt
        if self.wander_timer <= 0.0:
            self.is_resting = random.random() < 0.12
            self.wander_timer = random.uniform(0.6, 1.8)

        if self.is_resting:
            self.stop()
            self.action_text = "watch"
            return

        # 2) heading 을 조금씩만 회전(부드러운 곡선). dt 곱으로 프레임레이트 무관.
        self.heading += random.uniform(-70.0, 70.0) * dt
        direction = Vector2(1.0, 0.0).rotate(self.heading)
        cruise = self.speed * random.uniform(0.28, 0.40)
        self.desired_velocity = direction * cruise
        self.action_text = "wander"

    # ── 매 틱 갱신(자식이 오버라이드) ────────────────────────────────
    def update(self, world, dt):
        if not self.alive:
            return
        self.age += dt
        self.recover_stamina(dt)
        if not self.behave(world, dt):
            self.wander(dt)

    def behave(self, world, dt):
        """무엇을 할지 결정. 기본은 '결정 없음'(False). 종별로 오버라이드."""
        return False
