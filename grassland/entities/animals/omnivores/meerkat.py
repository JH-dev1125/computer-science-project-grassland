# =============================================================================
# meerkat.py — 미어캣 (계획서 Meerkat, Omnivore 상속)
# 고유 속성: is_sentinel(보초 중인가), sentinel_height(보초 시 높이)
# 고유 메서드: stand()(보초 서기), eat_grass()
# 위협 시 동굴(Cave)로 숨는다.
# =============================================================================
from grassland.config import MEERKAT_HOME_RADIUS
from grassland.entities.animals.omnivores.omnivore import Omnivore


class Meerkat(Omnivore):
    def __init__(self, position):
        # 체력 42, 속도 82(빠름), 공격력 5(약함), 감지 130, 반경 13(작음)
        super().__init__("Meerkat", position, (198, 157, 93),
                         health=42.0, speed=82.0, power=5.0,
                         detect_range=130.0, radius=13.0)
        self.diet_preference = 0.25   # 초식 선호 (0.25 = 주로 식물)
        self.aggression = 0.08        # 거의 싸우지 않음 (도망 위주)
        self.is_sentinel = False      # 현재 보초 중 여부
        self.sentinel_height = 0.0    # 보초 시 뒷발로 서는 높이 (렌더링용)

    def stand(self):
        # 뒷발로 서서 보초 개시: 이동 멈추고 sentinel 상태 활성화
        self.is_sentinel = True
        self.sentinel_height = 1.0
        self.stop()
        self.action_text = "stand"

    def eat_grass(self, grass):
        # 풀을 먹는 편의 메서드 → Omnivore.eat() 위임
        self.eat(grass)

    def behave(self, world, dt):
        # 보초 중이면 감지 범위 25% 확장
        threat = world.nearest_predator(
            self, self.detect_range * (1.25 if self.is_sentinel else 1.0))

        if threat is not None:
            # 위협 발견 → 가장 가까운 동굴로 도주
            cave = world.nearest_terrain_type("Cave", self.position)
            if cave is not None:
                self.move_toward(cave.position, self.speed * 1.2)  # 속도 120%로 질주
                if cave.contains(self):
                    # 동굴 안에 들어오면 은신 완료
                    self.is_hidden = True
                    self.stop()
                    self.action_text = "hide"
                else:
                    self.action_text = "cave"   # 아직 이동 중
                self.lose_energy(5.0 * dt)      # 도주 에너지 소모
                return True
            # 동굴이 없으면 Omnivore 기본 도망/맞섬 처리
            self.flee_or_fight(threat, world, dt)
            return True

        # 동굴에서 너무 멀어졌으면 복귀
        cave = world.nearest_terrain_type("Cave", self.position)
        if cave is not None and self.distance_to(cave) > MEERKAT_HOME_RADIUS:
            self.move_toward(cave.position, self.speed)
            self.action_text = "return"
            self.lose_energy(4.0 * dt)
            return True

        # 안전하고 배·갈증 모두 여유로우면 보초 서기
        if self.hunger < 70.0 and self.thirst < 70.0:
            self.stand()
            return True

        # 배고프거나 목마르면 보초 해제 후 Omnivore 기본 행동(먹기/마시기)
        self.is_sentinel = False
        self.sentinel_height = 0.0
        return super().behave(world, dt)
