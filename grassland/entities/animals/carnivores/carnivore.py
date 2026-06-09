# =============================================================================
# carnivore.py — 포식자 부모 (계획서 Carnivore)
# 고유 속성: stealth, acceleration, hunt_stamina_cost (detect_range 는 Animal 상속)
# 고유 메서드: hunt(), hide(), rest(), detect(), find_prey(), eat()(오버라이딩)
# =============================================================================
from grassland.entities.animals.animal import Animal
from grassland.entities.resources.carcass import Carcass


class Carnivore(Animal):
    def __init__(self, name, position, color,
                 health=100.0, speed=78.0, power=18.0, detect_range=160.0):
        super().__init__(name, position, color, health, speed, power,
                         detect_range, radius=20)
        self.diet_type = "carnivore"
        self.stealth = 0.18              # 피식자 panic_range 를 줄이는 은신율
        self.acceleration = 34.0         # 추격 순간 속도 증가량
        self.hunt_stamina_cost = 10.0    # 추격 1틱당 스태미나 소모

    def update(self, world, dt):
        if not self.alive:
            return
        self.age += dt
        self.hunger = min(100.0, self.hunger + 1.5 * dt)
        self.thirst = min(100.0, self.thirst + 0.65 * dt)
        self.recover_stamina(dt)
        if not self.behave(world, dt):
            self.wander(dt)

    def _elephant_near(self, world, pos, radius=90.0):
        """pos 주변에 코끼리가 있으면 True — 접근 전 사전 확인용."""
        return world.nearest_named("Elephant", pos, radius) is not None

    def behave(self, world, dt):
        # 1순위: 즉각적 위협 — 코끼리 회피 (범위 확대로 선제 회피)
        elephant = world.nearest_named("Elephant", self.position, 90.0)
        if elephant is not None and self.distance_to(elephant) < 90.0:
            self.move_away_from(elephant.position, self.speed)
            self.action_text = "avoid"
            return True
        # 2순위: 극도 굶주림 — 단, 목표 주변에 코끼리 없을 때만 접근
        if self.hunger > 72.0:
            carcass = world.nearest_carcass(self.position)
            if carcass is not None and not self._elephant_near(world, carcass.position):
                self.interaction_target = carcass
                if self.distance_to(carcass) <= self.radius + carcass.radius + 8:
                    self.eat(carcass)
                    self.stop()
                else:
                    self.move_toward(carcass.position, self.speed * 0.75)
                    self.action_text = "carcass"
                return True
            prey = self.find_prey(world)
            if prey is not None and not self._elephant_near(world, prey.position):
                self.hunt(prey, world, dt)
                return True
        # 3순위: 갈증 해소
        if self.seek_water_if_needed(world):
            return True
        # 4순위: 일반 배고픔 — 코끼리 없는 목표만
        if self.hunger > 45.0:
            carcass = world.nearest_carcass(self.position)
            if carcass is not None and not self._elephant_near(world, carcass.position):
                self.interaction_target = carcass
                if self.distance_to(carcass) <= self.radius + carcass.radius + 8:
                    self.eat(carcass)
                    self.stop()
                else:
                    self.move_toward(carcass.position, self.speed * 0.75)
                    self.action_text = "carcass"
                return True
            prey = self.find_prey(world)
            if prey is not None and not self._elephant_near(world, prey.position):
                self.hunt(prey, world, dt)
                return True
        return False

    def eat(self, food):
        """사체면 being_eaten_by 를 표시(하이에나 탈취·사자 포효 상호작용에 사용)."""
        if isinstance(food, Carcass):
            food.reduce_hunger(self)
            food.being_eaten_by = self
            self.action_text = "eat_carcass"
        else:
            super().eat(food)

    def hunt(self, prey, world, dt):
        if self.stamina <= 8.0:               # 지치면 추격 포기·휴식
            self.rest()
            return
        self.interaction_target = prey
        if self.distance_to(prey) <= self.radius + prey.radius + 8:
            self.attack(prey, world)
        else:
            self.move_toward(prey.position, self.speed + self.acceleration)
            self.action_text = "hunt"
        self.lose_energy(self.hunt_stamina_cost * dt)

    def hide(self):
        self.is_hidden = True
        self.action_text = "hide"

    def rest(self):
        self.stop()
        self.recover_stamina(0.8)
        self.action_text = "rest"

    def detect(self, target):
        """숨은 대상은 탐지 불가. 노출된 대상만 detect_range 안이면 탐지."""
        if getattr(target, "is_hidden", False):
            return False
        return self.distance_to(target) <= self.detect_range

    def find_prey(self, world):
        prey = world.nearest_prey_for(self, self.detect_range)
        if prey is not None and self.detect(prey):
            return prey
        return None
