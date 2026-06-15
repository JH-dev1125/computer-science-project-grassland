# =============================================================================
# environment.py — 환경 시스템 (역할: 시간·날씨·온도·이벤트)
# 좌표를 가진 '사물'이 아니라 맵 전체에 작용하는 '시스템'이라 Entity 가 아니다.
# world 가 Environment 인스턴스를 하나 들고 매 프레임 update() 를 호출한다.
# =============================================================================
#
#  [실행 흐름에서의 위치]
#    World.__init__ 이 self.environment = Environment() 로 객체를 하나 만들고,
#    매 프레임 world.update() 의 '1단계'에서 environment.update(dt) 를 부른다.
#    날씨/온도가 바뀌면 식물 성장·전투력·갈증 등에 쓰이는 '계수'를 다른 코드가 읽어 간다.
# =============================================================================
import random  # [문법] 표준 라이브러리. 날씨/온도 무작위 결정에 사용.

# [흐름 0] config 에서 시간 관련 상수 두 개만 가져온다(import 시 1회).
from grassland.config import DAY_LENGTH_HOURS, GAME_HOURS_PER_SECOND


WEATHER_PERIOD_HOURS = 6   # [변수] 날씨·온도가 바뀌는 주기(게임 내 시간) — 하루 4번 바뀐다


class Environment:
    """게임 내 시간·날씨·온도와 종료 여부를 관리.
    날씨/온도는 게임 내 6시간마다 바뀌고, growth/heat/combat 계수로 동·식물에 영향을 준다."""
    def __init__(self):
        # [←호출] World.__init__ 에서 Environment() 로 생성.
        self.day = 1               # [변수] 현재 게임 날짜(1부터 시작)
        self.time = 6.0            # [변수] 현재 시각(시 단위, 6.0=아침 6시)
        self.weather = "sunny"     # [변수] 현재 날씨: sunny / cloudy / rain / drought
        self.temperature = 28      # [변수] 현재 온도(℃)
        self._weather_hours = 0.0  # [변수] 마지막 날씨 변경 이후 누적된 게임 시간(6시간마다 변경 트리거)
        self.ended = False         # [변수] 시뮬레이션 종료 여부(미어캣 엔딩 시 True)
        self.end_reason = ""       # [변수] 종료 사유 문구(종료 화면에 표시)

    def update(self, dt):
        """dt(초)만큼 시간 진행. 하루가 넘어가면 True 반환."""
        # [←호출] world.update() 1단계.
        previous_day = self.day                       # 진행 전 날짜 기억
        self.change_time(dt * GAME_HOURS_PER_SECOND)  # 실제 초 → 게임 시간으로 환산해 진행
        return self.day != previous_day               # 날짜가 바뀌었으면 True(→ world.on_new_day)

    def change_time(self, hours):
        """게임 시간을 hours 만큼 진행하며 날씨·날짜 변경을 처리."""
        self.time += hours
        # 6시간마다 날씨·온도 변경(날짜와 독립)
        self._weather_hours += hours
        # [문법] while : 한 프레임에 6시간 이상 흘렀을 수 있어(배속), '넘긴 만큼' 여러 번 처리.
        while self._weather_hours >= WEATHER_PERIOD_HOURS:
            self._weather_hours -= WEATHER_PERIOD_HOURS
            self.change_weather()
            self.change_temp()
        # 자정을 넘기면 날짜만 증가
        while self.time >= DAY_LENGTH_HOURS:
            self.time -= DAY_LENGTH_HOURS
            self.day += 1

    def change_weather(self):
        """날씨를 네 종류 중 무작위로 새로 정한다."""
        self.weather = random.choice(["sunny", "cloudy", "rain", "drought"])

    def change_temp(self):
        """현재 날씨에 맞는 온도 범위에서 무작위로 온도를 정한다."""
        # [문법] random.randint(a, b) : a~b 사이 정수 난수(양 끝 포함).
        if self.weather == "drought":
            self.temperature = random.randint(34, 42)   # 가뭄: 무더움
        elif self.weather == "rain":
            self.temperature = random.randint(20, 28)    # 비: 선선
        elif self.weather == "cloudy":
            self.temperature = random.randint(23, 31)    # 흐림: 보통
        else:
            self.temperature = random.randint(27, 36)    # 맑음: 따뜻

    # ── 동·식물에 주는 영향 계수(다른 시스템이 읽어 곱해 쓴다) ──────────
    # [설계] 환경은 동물을 직접 안 건드린다. 대신 '배율(계수)'만 내놓고,
    #        그 값을 plant.update / world.apply_weather_effects / animal.attack 이 곱해 쓴다(느슨한 결합).
    def growth_multiplier(self):
        """식물 성장·번식 속도 배율. 비 오면 쑥쑥, 가뭄이면 시든다."""
        # [문법] {딕셔너리}[self.weather] : 현재 날씨를 '키'로 그 배율을 바로 꺼낸다.
        return {"rain": 1.9, "cloudy": 1.15, "sunny": 1.0, "drought": 0.35}[self.weather]

    def heat_factor(self):
        """더위 강도(0~). 26도에서 0, 더울수록 커진다 → 갈증·기력 소모를 키운다."""
        return max(0.0, (self.temperature - 26) / 12.0)

    def combat_factor(self):
        """전투력 배율. 무더운 가뭄엔 늘어져 공격이 약해지고, 선선하면 정상~약간 강."""
        return {"rain": 1.05, "cloudy": 1.0, "sunny": 1.0, "drought": 0.85}[self.weather]

    def clock_text(self):
        """'HH:MM' 형식 (UI 표시용)."""
        hour = int(self.time)                       # 정수부 = 시
        minute = int((self.time - hour) * 60)       # 소수부 × 60 = 분
        # [문법] f"{hour:02d}" : 두 자리 정수로(부족하면 앞에 0). 예: 6 → "06".
        return f"{hour:02d}:{minute:02d}"


class DroughtEvent:
    """가뭄 이벤트: drought 동안 물웅덩이를 말려간다(계획서 dry_up_map)."""
    # [←호출] world.apply_environment_events 가 가뭄일 때 이 객체를 만들어 매 프레임 dry_up_map 호출.
    def __init__(self, drought_intensity):
        self.drought_intensity = drought_intensity   # [변수] 가뭄 강도 0.5~1.0(클수록 빨리 마름)

    def dry_up_map(self, world, dt):
        """모든 물웅덩이의 물을 강도에 비례해 조금씩 줄인다(0이 되면 웅덩이 소멸)."""
        for puddle in world.water_puddles():
            puddle.consume(dt * self.drought_intensity * 3.0)   # [호출→] WaterPuddle.consume
