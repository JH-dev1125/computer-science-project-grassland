# =============================================================================
# carnivore.py — 포식자 부모 (계획서 Carnivore)
# 고유 속성: stealth, acceleration, hunt_stamina_cost (detect_range 는 Animal 상속)
# 고유 메서드: hunt(), hide(), rest(), detect(), find_prey(), eat()(오버라이딩)
# =============================================================================
#
#  [실행 흐름에서의 위치]
#    Lion/Hyena/BaldEagle 의 부모. world.update() 3단계에서 carnivore.update() 가 불리고,
#    그 안의 behave() 가 포식자의 '판단 우선순위'를 정한다:
#        ① 코끼리 회피  → ② 물  → ③ 먹이(사체·산 사냥감)  → ④ 덤불 매복(ambush)
#    종별 클래스(Lion 등)는 이 behave() 를 더 정교하게 다시 오버라이드한다.
# =============================================================================
from grassland.entities.animals.animal import Animal     # 부모(공통 AI)
from grassland.entities.resources.carcass import Carcass  # isinstance 로 '사체' 판별에 사용


class Carnivore(Animal):
    def __init__(self, name, position, color,
                 health=100.0, speed=78.0, power=18.0, detect_range=160.0):
        # [흐름] Animal.__init__ 을 먼저 호출(스탯·랜덤워크 상태 세팅). radius 는 20으로 고정.
        super().__init__(name, position, color, health, speed, power,
                         detect_range, radius=20)
        self.diet_type = "carnivore"     # [변수] 식성 표시(피식자가 '포식자'로 인식하는 기준)
        self.stealth = 0.18              # [변수] 은신율 — 피식자의 탐지 거리를 줄인다(높을수록 안 들킴)
        self.acceleration = 34.0         # [변수] 추격 순간 속도 증가량(사냥 시 speed 에 더해짐)
        self.hunt_stamina_cost = 8.0     # [변수] 추격 1틱당 스태미나 소모
        # [문법] set() : 중복 없는 집합. id 를 빠르게 'in' 검사하려고 리스트 대신 집합을 쓴다.
        self._finished_carcasses = set()  # [변수] 잔량 50% 미만이라 포기한 사체 id 들(다시 안 감)
        self._ambush_mode = False        # [변수] 매복 중 '공격 상태'인가 — 히스테리시스로 떨림 방지

    def update(self, world, dt):
        """포식자 매 프레임 진입점. (Animal.update 를 오버라이드해 허기/갈증 증가를 추가)"""
        # [←호출] world.update() 3단계.
        if not self.alive:
            return
        self.age += dt
        # 1.3으로 낮춰 포식자가 더 여유 있게 사냥 — 너무 자주 사냥해 먹이가 고갈되는 문제 완화
        self.hunger = min(100.0, self.hunger + 1.3 * dt)    # 시간이 지나며 배고파짐
        self.thirst = min(100.0, self.thirst + 0.65 * dt)   # 목말라짐
        self.recover_stamina(dt)
        if not self.behave(world, dt):    # [호출→] behave (못 정하면)
            self.wander(world, dt)        # [호출→] 어슬렁

    def _elephant_near(self, world, pos, radius=90.0):
        """pos 주변에 코끼리가 있으면 True — 접근 전 사전 확인용."""
        # [문법] 'X is not None' : 무언가를 찾았으면 True. 코끼리 근처 먹이엔 접근하지 않으려는 안전장치.
        return world.nearest_named("Elephant", pos, radius) is not None

    def behave(self, world, dt):
        """포식자 기본 판단 순서. True 를 돌려주면 update 가 wander 를 건너뛴다."""
        # ① 코끼리가 가까우면 도망(코끼리는 포식자를 쫓아냄)
        elephant = world.nearest_named("Elephant", self.position, 90.0)
        if elephant is not None and self.distance_to(elephant) < 90.0:
            self.move_away_from(elephant.position, self.speed)
            self.action_text = "avoid"
            return True
        # ② 목마르면 물
        if self.seek_water_if_needed(world):   # [호출→] Animal.seek_water_if_needed
            return True
        # ③ 배고프면 먹이(사체→산 사냥감)
        if self.search_food(world, dt):        # [호출→] search_food
            return True
        # ④ 그 외 — 덤불 매복
        return self.ambush(world, dt)          # [호출→] ambush

    def search_food(self, world, dt):
        """배고프면 먹이를 찾아 다가가/사냥한다. (Animal 의 빈 search_food 를 오버라이드)"""
        threshold = 20.0 if self.stamina < 25.0 else 45.0   # 지치면 더 일찍 먹이 탐색
        if self.hunger < threshold:
            self._committed_food = None
            return False
        # committed target 유지 — 한 번 정한 먹이를 계속 쫓는다(자꾸 바꾸지 않음)
        if self._food_valid(self._committed_food):
            food = self._committed_food
            if hasattr(food, 'diet_type'):  # 살아있는 먹잇감(동물) → 사냥 계속
                self.hunt(food, world, dt)
            else:                           # 사체 → 다가가 먹기
                self.interaction_target = food
                if self.distance_to(food) <= self.radius + food.radius + 8:
                    self.eat(food)
                    self.stop()
                else:
                    self.move_toward(food.position, self.speed * 0.75)
                    self.action_text = "search_food"
            return True
        self._committed_food = None
        # 먼저 주인 없는 사체를 찾는다(블랙리스트 제외).
        carcass = self.nearest_available_carcass(world, self.food_range)
        if carcass is not None and not self._elephant_near(world, carcass.position):
            self._committed_food = carcass
            self.interaction_target = carcass
            if self.distance_to(carcass) <= self.radius + carcass.radius + 8:
                self.eat(carcass)
                self.stop()
            else:
                self.move_toward(carcass.position, self.speed * 0.75)
                self.action_text = "search_food"
            return True
        # 사체가 없으면 산 사냥감을 찾는다.
        prey = self.find_prey(world)
        if prey is not None and not self._elephant_near(world, prey.position):
            self._committed_food = prey
            self.hunt(prey, world, dt)
            return True
        return False

    def ambush(self, world, dt):
        """배고프면 가까운 덤불에 숨어 기다리다, 먹이가 사정권에 들면 덮친다(기습).
        숨은 동안엔 피식자에게 보이지 않아(nearest_predator 가 제외) 먹이가 가까이 온다.
        히스테리시스: 공격 진입 110px, 해제 135px → 경계에서 hide↔ambush 와리가리 방지."""
        if self.hunger <= 40.0:           # 덜 배고프면 매복 안 함
            self._ambush_mode = False
            return False
        bush = world.nearest_bush(self.position, 260.0)   # 가까운 덤불 찾기
        if bush is None:
            self._ambush_mode = False
            return False
        if self.distance_to(bush) <= bush.radius + self.radius + 6:   # 덤불 안에 들어왔으면
            # [변수] trigger_range : 공격을 트리거할 거리. 이미 공격 중이면 135로 넓혀 잘 안 풀리게(히스테리시스).
            trigger_range = 135.0 if self._ambush_mode else 110.0
            prey = world.nearest_prey_for(self, trigger_range)
            if prey is not None and not self._elephant_near(world, prey.position):
                self._ambush_mode = True
                self.is_hidden = False    # 덮치는 순간 모습을 드러냄
                self.stealth = 0.18
                self.hunt(prey, world, dt)   # [호출→] hunt(덮치기)
                self.action_text = "ambush"
            else:
                self._ambush_mode = False
                self.hide()               # [호출→] hide(계속 숨어 대기)
                self.stop()
            return True
        # 덤불이 멀면 그쪽으로 살금살금 이동(stalk)
        self._ambush_mode = False
        self.move_toward(bush.position, self.speed * 0.85)
        self.action_text = "stalk"
        return True

    def eat(self, food):
        """사체면 being_eaten_by 를 표시(하이에나 탈취 상호작용에 사용).
        eat 시도 시 사체 잔량이 50% 미만이면 블랙리스트에 추가하고 이탈."""
        # [문법] Animal.eat 을 오버라이드. 사체엔 특별 처리, 그 외엔 super().eat 으로 위임.
        if isinstance(food, Carcass):
            self.interaction_target = food
            self.action_text = "eat"
            if food.amount < food.max_amount * 0.5:   # 잔량 적은 사체는 포기하고 블랙리스트 등록
                self._finished_carcasses.add(food.id)
                return
            if self._feed_ready():
                food.reduce_hunger(self)
                food.being_eaten_by = self   # '내가 먹는 중'을 표시(하이에나가 이걸 보고 탈취)
        else:
            super().eat(food)             # 사체가 아니면 부모(Animal)의 일반 eat

    def nearest_available_carcass(self, world, max_distance=None):
        """블랙리스트(50% 미만 eat 시도)된 사체는 탐색에서 제외한다."""
        # [문법] world._nearest(목록, 위치, 조건함수, 최대거리) : 조건을 만족하는 가장 가까운 것.
        return world._nearest(world.carcasses(), self.position,
                              lambda c: c.id not in self._finished_carcasses
                                        and c.carried_by is None,
                              max_distance)

    def hunt(self, prey, world, dt):
        """먹이를 추격하고, 닿으면 공격한다. (Hyena/BaldEagle 이 다시 오버라이드)"""
        if self.stamina <= 8.0:               # 지치면 추격 포기·휴식
            self.rest(dt)
            return
        self.interaction_target = prey
        if self.distance_to(prey) <= self.radius + prey.radius + 8:   # 사정권 안 → 공격
            was_alive = prey.alive
            self.attack(prey, world)          # [호출→] Animal.attack
            if was_alive and not prey.alive:  # 이번 공격으로 죽였으면
                self.stop()
                self.action_text = "eat"
            self.lose_energy(7.0 * dt)
        else:
            # 예측 추격(lead pursuit): 먹이의 '갈 곳'을 노려 다양한 각도로 파고든다.
            # 먹이가 지그재그로 꺾으면 예측이 빗나가 포식자가 헛돈다(자연스러운 회피).
            lead = prey.position + prey.velocity * 0.35   # 먹이의 0.35초 뒤 예상 위치
            self.move_toward(lead, self.speed + self.acceleration)   # 가속 붙여 추격
            self.action_text = "hunt"
            self.lose_energy(self.hunt_stamina_cost * dt)

    def hide(self):
        """덤불에 숨는다. 스텔스 값을 높여 먹이가 더 가까이 올 때까지 못 알아채게 한다."""
        self.is_hidden = True
        self.stealth = 0.4    # 매복 중 stealth 0.18 → 0.4 로 높아짐(더 안 들킴)
        self.action_text = "hide"

    def rest(self, dt=0.016):
        """멈춰 기력을 빠르게 회복한다."""
        self.stop()
        self.stamina = min(100.0, self.stamina + 10.0 * dt)

    def detect(self, target):
        """숨은 대상은 탐지 불가. 노출된 대상만 detect_range 안이면 탐지."""
        if getattr(target, "is_hidden", False):
            return False
        return self.distance_to(target) <= self.detect_range

    def find_prey(self, world):
        """탐지 가능한 가장 가까운 사냥감을 돌려준다(없으면 None)."""
        prey = world.nearest_prey_for(self, self.detect_range)   # [호출→] World.nearest_prey_for
        if prey is not None and self.detect(prey):
            return prey
        return None
