from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from grassland.world import World
from grassland.entities.animals.animal import Animal
from grassland.geometry import Vec2


class Herbivore(Animal):
    def __init__(
        self,
        name: str,
        position: Vec2,
        color: tuple[int, int, int],
        health: float,
        speed: float,
        power: float,
        detect_range: float = 160.0,
    ):
        super().__init__(name, position, color, health, speed, power, detect_range)
        self.role = "herbivore"
        self.diet_type = "herbivore"
        self.flee_speed = speed * 1.25
        self.panic_range = detect_range
        self.base_panic_range = detect_range
        self.is_chased = False
        self.panic_boost_timer = 0.0
        # [추가] 번식 쿨다운 타이머: 너무 자주 번식하는 것을 방지하기 위한 대기 시간(초)
        # 0이 되어야 다시 번식을 시도할 수 있음
        self.reproduce_cooldown = 0.0

    def update(self, world: "World", dt: float) -> None:
        if not self.alive:
            return
        self.age += dt
        self.hunger = min(100.0, self.hunger + 2.4 * dt)
        self.thirst = min(100.0, self.thirst + 2.1 * dt)
        self.recover_stamina(dt)

        # panic_boost_timer 감소 및 패닉 상태일 때 감지 범위/스태미나 회복률 조절
        if self.panic_boost_timer > 0:
            self.panic_boost_timer = max(0.0, self.panic_boost_timer - dt)
            self.panic_range = self.base_panic_range * 2.0  # 패닉 시 감지 범위 2배 확장
            self.stamina_recovery_rate = 3.5  # 패닉 시 스태미나 회복 느려짐
        else:
            self.panic_range = self.base_panic_range
            self.stamina_recovery_rate = 7.0

        # [추가] 번식 쿨다운 타이머를 매 프레임 감소시킴
        # 기존에는 reproduce_cooldown 변수 자체가 없었음 → 번식 로직을 추가하면서 함께 추가
        if self.reproduce_cooldown > 0:
            self.reproduce_cooldown = max(0.0, self.reproduce_cooldown - dt)

        # [추가] 포식자가 없고(is_chased=False) 배가 어느 정도 불렀을 때(hunger<40) 체력 회복
        # 기존 문제: heal()이 메서드로 정의만 되어 있었고 update()/behave() 어디서도 호출하지 않아
        #            사실상 죽은 코드(dead code)였음 → 안전한 상황에서 호출하도록 수정
        if not self.is_chased and self.hunger < 40.0:
            self.heal()

        # [추가] 안전한 상태일 때 스트레스를 서서히 감소시킴
        # 기존 문제: Animal 클래스에 stress 변수가 정의되어 있었지만
        #            Herbivore에서 읽거나 쓰는 코드가 전혀 없어서 완전히 방치된 상태였음
        if not self.is_chased:
            self.stress = max(0.0, self.stress - 5.0 * dt)

        if not self.behave(world, dt):
            self.wander(dt)

    def behave(self, world: "World", dt: float) -> bool:
        threat = world.nearest_predator(self, self.panic_range)

        # [수정] 포식자를 처음 발견하는 순간(직전 프레임엔 쫓기지 않다가 이번에 위협 감지)
        # panic_boost_timer를 4.0초로 설정 → 패닉 부스트가 실제로 발동되게 됨
        #
        # 기존 코드의 핵심 버그:
        #   - panic_boost_timer의 초기값이 __init__에서 0.0으로 설정됨
        #   - update()에서는 타이머를 "감소"시키는 코드만 있고
        #   - 타이머를 "양수로 설정"하는 코드가 어디에도 없었음
        #   - 결과: 타이머가 한 번도 0보다 커진 적이 없어 panic 부스트가 절대 작동 안 됐음
        if threat is not None and not self.is_chased:
            self.panic_boost_timer = 4.0  # 포식자 첫 발견 시 4초간 패닉 상태 부여

        self.is_chased = threat is not None

        # [추가] 포식자에게 쫓기는 동안 매 프레임 스트레스 증가
        # stress 변수가 Animal에 있었지만 Herbivore에서 전혀 활용하지 않았음
        if self.is_chased:
            self.stress = min(100.0, self.stress + 15.0 * dt)

        if threat is not None:
            bush = world.nearest_bush(self.position, 95.0)
            if bush is not None and self.can_hide_in_bush():
                self.move_toward(bush.position, self.flee_speed)
                if self.position.distance_to(bush.position) < bush.radius + self.radius:
                    bush.hide_entity(self)
                return True
            self.fight_or_flight(threat, world, dt)
            return True

        # [추가] 안전하고 배부를 때(hunger<50) 번식 시도
        # 기존 문제: Animal 클래스에 couple() 메서드가 정의되어 있었지만
        #            Herbivore.behave()에서 전혀 호출되지 않아 번식이 일어나지 않았음
        if self.reproduce_cooldown <= 0 and self.hunger < 50.0:
            if self.try_reproduce(world):
                return True

        return self.seek_water_if_needed(world) or self.seek_plants_if_needed(world)

    def can_hide_in_bush(self) -> bool:
        return False

    def heal(self) -> None:
        # [수정] 메서드 자체는 기존에도 있었으나 어디서도 호출하지 않았음
        # → update()에서 안전 + 배부른 조건일 때 호출하도록 수정
        self.health = min(self.max_health, self.health + 3.0)

    def fight_or_flight(self, threat: Animal, world: Optional["World"], dt: float) -> None:
        # [수정] 기존 코드의 문제:
        #   - 메서드 이름이 fight_or_flight(싸우거나 도망)인데 항상 도망(flight)만 했음
        #   - self.attack() 호출 코드가 아예 없었음
        #
        # 수정 내용:
        #   - 체력 비율이 70% 초과이고 스태미나가 60 이상이면 반격(fight)
        #   - 그 외엔 기존처럼 도망(flight)
        #   - 이를 통해 elephant처럼 큰 초식동물이 방어적으로 반격하는 동작도 표현 가능
        health_ratio = self.health / self.max_health if self.max_health > 0 else 0.0
        if health_ratio > 0.7 and self.stamina > 60.0 and world is not None:
            # 체력·스태미나 충분 → 위협에 맞서 공격
            self.attack(threat, world)
            self.lose_energy(10.0 * dt)
            self.action_text = "fight"
        else:
            # 체력·스태미나 부족 → 도망
            self.move_away_from(threat.position, self.flee_speed)
            self.lose_energy(8.0 * dt)
            self.action_text = "flee"

    def try_reproduce(self, world: "World") -> bool:
        # [추가] 번식 메서드 신규 추가
        # 기존 문제: Animal.couple()이 정의되어 있었지만 Herbivore에서 전혀 사용하지 않았음
        #            → 초식동물 개체수가 전혀 늘어나지 않는 시뮬레이션 결함
        #
        # 동작 방식:
        #   1. 반경 80 안에 같은 종의 파트너를 탐색
        #   2. 파트너가 살아 있고 쿨다운이 끝났으면 couple() 시도
        #   3. couple()은 50% 확률로 True/False 반환 (Animal 클래스에 정의)
        #   4. 성공 시 world.spawn_offspring()으로 자손 생성, 양쪽 모두 쿨다운 30초 부여
        #   5. 실패해도 15초 쿨다운 부여 (같은 파트너와 매 프레임 시도하는 것 방지)
        # hasattr 가드: world 타입이 object로 선언되어 있어 IDE가 메서드를 못 찾는 문제 방지
        # world.py에 nearest_same_species / spawn_offspring 이 실제로 추가되어 있음
        partner = world.nearest_same_species(self, radius=80.0)
        if partner is None:
            return False
        if not partner.alive:
            return False
        if not isinstance(partner, Herbivore) or partner.reproduce_cooldown > 0:
            return False
        if self.couple(self, partner):
            world.spawn_offspring(self)
            self.reproduce_cooldown = 30.0
            partner.reproduce_cooldown = 30.0
            self.action_text = "reproduce"
        else:
            # 번식 실패해도 쿨다운 부여
            self.reproduce_cooldown = 15.0
        return True
