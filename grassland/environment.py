# =============================================================================
# environment.py — 환경 시스템 (역할: 시간·날씨·온도·이벤트)
# 좌표를 가진 '사물'이 아니라 맵 전체에 작용하는 '시스템'이라 Entity 가 아니다.
# world 가 Environment 인스턴스를 하나 들고 매 프레임 update() 를 호출한다.
# =============================================================================
import random

from grassland.config import DAY_LENGTH_HOURS, GAME_HOURS_PER_SECOND


WEATHER_PERIOD_HOURS = 6   # 날씨·온도가 바뀌는 주기(게임 내 시간) — 하루 4번 바뀐다


class Environment:
    """게임 내 시간·날씨·온도와 종료 여부를 관리.
    날씨/온도는 게임 내 6시간마다 바뀌고, growth/heat/combat 계수로 동·식물에 영향을 준다."""
    def __init__(self):
        self.day = 1
        self.time = 6.0            # 6시=아침
        self.weather = "sunny"     # sunny / cloudy / rain / drought
        self.temperature = 28
        self._weather_hours = 0.0  # 마지막 날씨 변경 이후 누적 시간
        self.ended = False
        self.end_reason = ""

    def update(self, dt):
        """dt(초)만큼 시간 진행. 하루가 넘어가면 True 반환."""
        previous_day = self.day
        self.change_time(dt * GAME_HOURS_PER_SECOND)
        return self.day != previous_day

    def change_time(self, hours):
        self.time += hours
        # 6시간마다 날씨·온도 변경(날짜와 독립)
        self._weather_hours += hours
        while self._weather_hours >= WEATHER_PERIOD_HOURS:
            self._weather_hours -= WEATHER_PERIOD_HOURS
            self.change_weather()
            self.change_temp()
        # 자정을 넘기면 날짜만 증가
        while self.time >= DAY_LENGTH_HOURS:
            self.time -= DAY_LENGTH_HOURS
            self.day += 1

    def change_weather(self):
        self.weather = random.choice(["sunny", "cloudy", "rain", "drought"])

    def change_temp(self):
        if self.weather == "drought":
            self.temperature = random.randint(34, 42)
        elif self.weather == "rain":
            self.temperature = random.randint(20, 28)
        elif self.weather == "cloudy":
            self.temperature = random.randint(23, 31)
        else:
            self.temperature = random.randint(27, 36)

    # ── 동·식물에 주는 영향 계수(다른 시스템이 읽어 곱해 쓴다) ──────────
    def growth_multiplier(self):
        """식물 성장·번식 속도 배율. 비 오면 쑥쑥, 가뭄이면 시든다."""
        return {"rain": 1.9, "cloudy": 1.15, "sunny": 1.0, "drought": 0.35}[self.weather]

    def heat_factor(self):
        """더위 강도(0~). 26도에서 0, 더울수록 커진다 → 갈증·기력 소모를 키운다."""
        return max(0.0, (self.temperature - 26) / 12.0)

    def combat_factor(self):
        """전투력 배율. 무더운 가뭄엔 늘어져 공격이 약해지고, 선선하면 정상~약간 강."""
        return {"rain": 1.05, "cloudy": 1.0, "sunny": 1.0, "drought": 0.85}[self.weather]

    def clock_text(self):
        """'HH:MM' 형식 (UI 표시용)."""
        hour = int(self.time)
        minute = int((self.time - hour) * 60)
        return f"{hour:02d}:{minute:02d}"


class DroughtEvent:
    """가뭄 이벤트: drought 동안 물웅덩이를 말려간다(계획서 dry_up_map)."""
    def __init__(self, drought_intensity):
        self.drought_intensity = drought_intensity   # 0.5~1.0

    def dry_up_map(self, world, dt):
        for puddle in world.water_puddles():
            puddle.consume(dt * self.drought_intensity * 3.0)
