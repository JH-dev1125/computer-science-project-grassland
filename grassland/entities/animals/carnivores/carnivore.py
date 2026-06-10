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
        self.hunt_stamina_cost = 8.0     # 추격 1틱당 스태미나 소모
        self._finished_carcasses = set()  # eat 시도 시 50% 미만이면 영구 블랙리스트
        self._ambush_mode = False        # 매복 중 공격 상태 — 히스테리시스로 와리가리 방지

    def update(self, world, dt):
        if not self.alive:
            return
        self.age += dt
        # 1.3으로 낮춰 포식자가 더 여유 있게 사냥 — 너무 자주 사냥해 먹이가 고갈되는 문제 완화
        self.hunger = min(100.0, self.hunger + 1.3 * dt)
        self.thirst = min(100.0, self.thirst + 0.65 * dt)
        self.recover_stamina(dt)
        if not self.behave(world, dt):
            self.wander(world, dt)

    def _elephant_near(self, world, pos, radius=90.0):
        """pos 주변에 코끼리가 있으면 True — 접근 전 사전 확인용."""
        return world.nearest_named("Elephant", pos, radius) is not None

    def behave(self, world, dt):
        elephant = world.nearest_named("Elephant", self.position, 90.0)
        if elephant is not None and self.distance_to(elephant) < 90.0:
            self.move_away_from(elephant.position, self.speed)
            self.action_text = "avoid"
            return True
        if self.seek_water_if_needed(world):
            return True
        if self.search_food(world, dt):
            return True
        return self.ambush(world, dt)

    def search_food(self, world, dt):
        if self.hunger < 45.0:
            return False
        carcass = self.nearest_available_carcass(world, self.food_range)
        if carcass is not None and not self._elephant_near(world, carcass.position):
            self.interaction_target = carcass
            if self.distance_to(carcass) <= self.radius + carcass.radius + 8:
                self.eat(carcass)
                self.stop()
            else:
                self.move_toward(carcass.position, self.speed * 0.75)
                self.action_text = "search_food"
            return True
        prey = self.find_prey(world)
        if prey is not None and not self._elephant_near(world, prey.position):
            self.hunt(prey, world, dt)
            return True
        return False

    def ambush(self, world, dt):
        """배고프면 가까운 덤불에 숨어 기다리다, 먹이가 사정권에 들면 덮친다(기습).
        숨은 동안엔 피식자에게 보이지 않아(nearest_predator 가 제외) 먹이가 가까이 온다.
        히스테리시스: 공격 진입 110px, 해제 135px → 경계에서 hide↔ambush 와리가리 방지."""
        if self.hunger <= 40.0:
            self._ambush_mode = False
            return False
        bush = world.nearest_bush(self.position, 260.0)
        if bush is None:
            self._ambush_mode = False
            return False
        if self.distance_to(bush) <= bush.radius + self.radius + 6:
            # 공격 중이면 135px까지 유지, 대기 중이면 110px 진입 시 공격
            trigger_range = 135.0 if self._ambush_mode else 110.0
            prey = world.nearest_prey_for(self, trigger_range)
            if prey is not None and not self._elephant_near(world, prey.position):
                self._ambush_mode = True
                self.is_hidden = False
                self.stealth = 0.18
                self.hunt(prey, world, dt)
                self.action_text = "ambush"
            else:
                self._ambush_mode = False
                self.hide()
                self.stop()
            return True
        self._ambush_mode = False
        self.move_toward(bush.position, self.speed * 0.85)
        self.action_text = "stalk"
        return True

    def eat(self, food):
        """사체면 being_eaten_by 를 표시(하이에나 탈취 상호작용에 사용).
        eat 시도 시 사체 잔량이 50% 미만이면 블랙리스트에 추가하고 이탈."""
        if isinstance(food, Carcass):
            self.interaction_target = food
            self.action_text = "eat"
            if food.amount < food.max_amount * 0.5:
                self._finished_carcasses.add(food.id)
                return
            if self._feed_ready():
                food.reduce_hunger(self)
                food.being_eaten_by = self
        else:
            super().eat(food)

    def nearest_available_carcass(self, world, max_distance=None):
        """블랙리스트(50% 미만 eat 시도)된 사체는 탐색에서 제외한다."""
        return world._nearest(world.carcasses(), self.position,
                              lambda c: c.id not in self._finished_carcasses
                                        and c.carried_by is None,
                              max_distance)

    def hunt(self, prey, world, dt):
        if self.stamina <= 8.0:               # 지치면 추격 포기·휴식
            self.rest(dt)
            return
        self.interaction_target = prey
        if self.distance_to(prey) <= self.radius + prey.radius + 8:
            was_alive = prey.alive
            self.attack(prey, world)
            if was_alive and not prey.alive:
                self.stop()
                self.action_text = "eat"
            self.lose_energy(7.0 * dt)
        else:
            # 예측 추격(lead pursuit): 먹이의 '갈 곳'을 노려 다양한 각도로 파고든다.
            # 먹이가 지그재그로 꺾으면 예측이 빗나가 포식자가 헛돈다(자연스러운 회피).
            lead = prey.position + prey.velocity * 0.35
            self.move_toward(lead, self.speed + self.acceleration)
            self.action_text = "hunt"
            self.lose_energy(self.hunt_stamina_cost * dt)

    def hide(self):
        """덤불에 숨는다. 스텔스 값을 높여 먹이가 더 가까이 올 때까지 못 알아채게 한다."""
        self.is_hidden = True
        self.stealth = 0.4    # 매복 중 stealth 0.18 → 0.4 로 높아짐
        self.action_text = "hide"

    def rest(self, dt=0.016):
        self.stop()
        self.stamina = min(100.0, self.stamina + 10.0 * dt)

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
