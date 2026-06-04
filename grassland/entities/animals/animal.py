# =============================================================================
# entities/animals/animal.py — 모든 동물의 공통 부모 (계획서 Animal)
# 계획서에 명시된 공통 속성/메서드만 둔다. 종별 행동은 자식이 오버라이드.
# =============================================================================
import random

from grassland.entities.base import Entity
from grassland.geometry import Vec2, random_unit_vector


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
        self.decision_timer = random.uniform(0.2, 1.4)
        self._carcass_spawned = False

    # ── 계획서 공통 메서드 ───────────────────────────────────────────
    def move(self, direction):
        self.velocity = direction.normalized() * self.speed

    def eat(self, food):
        """food 는 consume(amount) 또는 reduce_hunger(self) 를 가진 객체(덕 타이핑)."""
        if hasattr(food, "reduce_hunger"):        # 사체 등
            food.reduce_hunger(self)
        elif hasattr(food, "consume"):            # 식물 등
            eaten = food.consume(14)
            self.hunger = max(0.0, self.hunger - eaten)
        self.action_text = "eat"

    def drink(self, source):
        """source 는 reduce_thirst(self) 또는 enable_drinking(self) 를 가진 객체."""
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
        self.stop()
        self.action_text = "dead"
        if world is not None and not self._carcass_spawned:
            self._carcass_spawned = True
            world.spawn_carcass(self)        # 죽으면 사체 생성

    def status(self):
        return super().status()

    def distant_to(self, target):            # 계획서 표기(distant_to) 유지
        return self.distance_to(target)

    def attack(self, target, world):
        if not target.alive:
            return
        target.health -= self.power
        target.stress = min(100.0, target.stress + 8.0)
        self.action_text = "attack"
        if target.health <= 0:
            target.die(world)

    def couple(self, one, other):
        """번식 성공 여부(확률 1/2). World 가 호출해 새 개체를 만든다."""
        if one.alive and other.alive:
            return bool(round(random.uniform(0, 1)))
        return False

    def recover_stamina(self, dt):
        self.stamina = min(100.0, self.stamina + self.stamina_recovery_rate * dt)

    # ── 공통 행동 보조(여러 종이 공유) ───────────────────────────────
    def seek_water_if_needed(self, world):
        """목이 마르면 가장 가까운 물로 이동·음수. 행동했으면 True."""
        if self.thirst < 58.0:
            return False
        water = world.nearest_water(self.position)
        if water is None:
            return False
        if self.distance_to(water) <= self.radius + water.radius + 8:
            self.drink(water)
            self.stop()
        else:
            self.move_toward(water.position, self.speed * 0.85)
            self.action_text = "water"
        return True

    def seek_plants_if_needed(self, world):
        """배고프면 가장 가까운 식물로 이동·섭취. 행동했으면 True."""
        if self.hunger < 62.0:
            return False
        plant = world.nearest_plant(self.position)
        if plant is None:
            return False
        if self.distance_to(plant) <= self.radius + plant.radius + 8:
            self.eat(plant)
            self.stop()
        else:
            self.move_toward(plant.position, self.speed * 0.7)
            self.action_text = "graze"
        return True

    def wander(self, dt):
        """할 일이 없을 때 무작위로 어슬렁."""
        self.decision_timer -= dt
        if self.decision_timer > 0:
            return
        self.decision_timer = random.uniform(0.8, 2.2)
        if random.random() < 0.22:
            self.stop()
            self.action_text = "watch"
            return
        self.velocity = random_unit_vector() * random.uniform(
            self.speed * 0.18, self.speed * 0.45)
        self.action_text = "move"

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
