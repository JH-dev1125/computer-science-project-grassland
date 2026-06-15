# =============================================================================
# herbivore.py — 초식동물 부모 (계획서 Herbivore)
# 고유 속성: panic_range(도주 감지 거리), is_chased, stress, _escape_luck(도주 운)
# 고유 메서드: behave(위협 우선), fight_or_flight(), heal(), search_food(풀 먹기)
# =============================================================================
#
#  [실행 흐름에서의 위치]
#    Zebra/Gazelle/Elephant 의 부모. world.update() 3단계에서 herbivore.update() 호출.
#    behave() 의 1순위는 '포식자 감지'다: 위협이 보이면 도주(또는 덤불 은신/반격),
#    위협이 없으면 → 물 → 풀 먹기 순서. 종별로 fight_or_flight 를 다르게 오버라이드한다
#    (얼룩말=뒷발차기, 가젤=지그재그, 코끼리=짓밟기).
# =============================================================================
# [문법] from __future__ import annotations : 타입 힌트를 늦게 평가(전방 참조 허용).
from __future__ import annotations
import random
# [문법] Optional["World"] = World 또는 None 일 수 있다는 타입 힌트. TYPE_CHECKING 으로 순환 import 회피.
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from grassland.world import World
from grassland.entities.animals.animal import Animal   # 부모(공통 AI)
from pygame.math import Vector2


class Herbivore(Animal):
    def __init__(
        self,
        name: str,
        position: Vector2,
        color: tuple[int, int, int],
        health: float,
        speed: float,
        power: float,
        detect_range: float = 110.0,
    ):
        # [흐름] Animal.__init__ 으로 공통 스탯 세팅.
        super().__init__(name, position, color, health, speed, power, detect_range)
        self.role = "herbivore"
        self.diet_type = "herbivore"             # [변수] 식성(포식자가 사냥감으로 인식)
        self.panic_range = detect_range          # [변수] 현재 도주 감지 거리(경고 받으면 일시 2배)
        self.base_panic_range = detect_range     # [변수] 기본 도주 감지 거리(원상 복귀 기준)
        self.is_chased = False                   # [변수] 지금 쫓기는 중인가
        self.panic_boost_timer = 0.0             # [변수] 경고로 감지 범위가 2배가 되는 남은 시간
        self.reproduce_cooldown = 0.0            # [변수] 번식 쿨다운(현재 거의 미사용)
        self.flee_timer = 0.0                    # [변수] 위협을 본 뒤 계속 도주하는 잔여 시간
        self._last_threat_pos = None             # [변수] 마지막으로 본 위협 위치(시야에서 사라져도 그쪽 반대로 도주)
        # 도주 운(luck): 매 1~3초마다 새로 굴려 실제 도주속도와 기동성을 살짝 변화시킨다.
        # 개체마다 다른 타이밍으로 굴러 떼가 엇갈리게 흩어지는 자연스러운 효과.
        self._escape_luck = 1.0                  # [변수] 도주 속도 배율(0.65~1.45)
        self._escape_luck_timer = random.uniform(0.5, 2.0)  # [변수] 다음 luck 갱신까지 시간

    def update(self, world: "World", dt: float) -> None:
        """초식 매 프레임 진입점(Animal.update 오버라이드 — 허기/갈증·패닉·치유 추가)."""
        # [←호출] world.update() 3단계.
        if not self.alive:
            return
        self.age += dt
        self.hunger = min(100.0, self.hunger + 1.2 * dt)
        self.thirst = min(100.0, self.thirst + 0.55 * dt)
        self.recover_stamina(dt)
        if self.panic_boost_timer > 0:           # 경고를 받은 상태면 감지 범위 2배
            self.panic_boost_timer = max(0.0, self.panic_boost_timer - dt)
            self.panic_range = self.base_panic_range * 2.0
        else:
            self.panic_range = self.base_panic_range
        if self.reproduce_cooldown > 0:
            self.reproduce_cooldown = max(0.0, self.reproduce_cooldown - dt)
        if not self.is_chased and self.hunger < 40.0:
            self.heal(dt)                        # 안전하고 안 배고프면 체력 회복
        if not self.is_chased:
            self.stress = max(0.0, self.stress - 5.0 * dt)   # 안전하면 스트레스 감소
        if not self.behave(world, dt):           # [호출→] behave
            self.wander(world, dt)

    def behave(self, world: "World", dt: float) -> bool:
        """초식 판단: 위협 감지 → 도주/은신/반격. 없으면 물·먹이."""
        # 스트레스가 높을수록 포식자를 더 멀리서 감지한다(지속적인 경계 상태 반영).
        # stress=0 → 기본 범위, stress=100 → 최대 40px 추가. 이산적 배수가 아닌 연속 증가.
        stress_bonus = self.stress * 0.40
        effective_panic_range = self.panic_range + stress_bonus
        threat = world.nearest_predator(self, effective_panic_range)   # [호출→] World.nearest_predator
        if threat is not None:
            self._last_threat_pos = threat.position.copy()   # 위치 복사(원본이 움직여도 기억은 고정)
            self.flee_timer = 2.5                            # 2.5초간 계속 도주
            if not self.is_chased:
                self.panic_boost_timer = 4.0                 # 막 발견 순간 경계 4초 강화
        self.flee_timer = max(0.0, self.flee_timer - dt)
        self.is_chased = self.flee_timer > 0.0
        if self.is_chased:
            self.stress = min(100.0, self.stress + 15.0 * dt)
            # 도주 운 타이머 갱신 — 1~3초마다 새 luck 값을 굴린다
            self._escape_luck_timer -= dt
            if self._escape_luck_timer <= 0.0:
                # [문법] random.triangular(저, 고, 최빈) : 삼각분포. 대부분 1.0 근처, 가끔 0.65/1.45.
                self._escape_luck = random.triangular(0.65, 1.45, 1.0)
                self._escape_luck_timer = random.uniform(1.0, 3.0)
            if threat is not None:               # 위협이 아직 보이면
                self.interaction_target = threat
                bush = world.nearest_bush(self.position, 95.0)
                if bush is not None and self.can_hide_in_bush():   # 숨을 수 있는 종이면 덤불로
                    self.move_toward(bush.position, self.flee_speed)
                    if self.position.distance_to(bush.position) < bush.radius + self.radius:
                        bush.hide_entity(self)   # [호출→] Bush.hide_entity(은신)
                    return True
                self.fight_or_flight(threat, world, dt)   # [호출→] 반격 또는 도주(종별 오버라이드)
            else:                                # 위협이 시야에서 사라졌으면 마지막 위치 반대로 도주
                self.interaction_target = None
                self.evade(self._last_threat_pos, self.flee_speed * self._escape_luck, dt)
            return True
        # [문법] A or B : A 가 True(행동함)면 거기서 끝, 아니면 B 를 시도. (물 우선, 그다음 먹이)
        return self.seek_water_if_needed(world) or self.search_food(world, dt)

    def search_food(self, world, dt):
        """배고프면 가까운 풀로 가서 먹는다(Animal 의 빈 search_food 오버라이드)."""
        threshold = 20.0 if self.stamina < 25.0 else 40.0
        if self.hunger < threshold:
            self._committed_food = None
            return False
        # 이미 정한 풀이 유효하면 유지, 아니면 새로 찾는다.
        plant = self._committed_food if self._food_valid(self._committed_food) else None
        if plant is None:
            reach = None if self.hunger > 92.0 else self.food_range   # 아주 배고프면 거리 무제한
            plant = world.nearest_plant(self.position, reach)
            if plant is None:
                return False
            self._committed_food = plant
        self.interaction_target = plant
        if self.distance_to(plant) <= self.radius + plant.radius + 8:
            self.eat(plant)                      # [호출→] Animal.eat → Plant.consume
            self.stop()
        else:
            self.move_toward(plant.position, self.speed * 0.7)
            self.action_text = "search_food"
        return True

    def can_hide_in_bush(self) -> bool:
        """덤불에 숨을 수 있는 종인가. 기본은 False(현재 어떤 초식도 덤불 은신을 안 함)."""
        return False

    def heal(self, dt: float) -> None:
        """안전할 때 체력 회복(스트레스가 높으면 더 느리게)."""
        # 스트레스가 높으면 회복이 느려진다(stress=0 → 4.0/s, stress=100 → 2.0/s).
        # 이산 임계값 없이 스트레스 수치에 비례해 연속적으로 감소.
        stress_penalty = self.stress * 0.020   # 최대 2.0 감소(스트레스 100)
        self.health = min(self.max_health, self.health + max(0.5, 4.0 - stress_penalty) * dt)

    @property
    def flee_speed(self):
        """도주 속도 = 기본 속도의 1.25배(읽을 때마다 계산)."""
        return self.speed * 1.25

    def fight_or_flight(
        self, threat: Animal, world: Optional["World"], dt: float
    ) -> None:
        """건강하면 맞서고, 아니면 도망. (Zebra/Gazelle/Elephant 이 다르게 오버라이드)"""
        health_ratio = self.health / self.max_health if self.max_health > 0 else 0.0
        if health_ratio > 0.7 and self.stamina > 60.0 and world is not None:
            self.attack(threat, world)           # 체력·기력 충분 → 반격
            self.lose_energy(7.0 * dt)
        else:
            # 도주 속도에 luck 배율 적용 — 운이 좋은 순간엔 탈출, 나쁘면 따라잡힌다
            # evade() 내부에서 -5/s 소모
            self.evade(threat.position, self.flee_speed * self._escape_luck, dt)
