# =============================================================================
# environment.py — 환경 시스템 (역할: 시간·날씨·온도·이벤트)
# 좌표를 가진 '사물'이 아니라 맵 전체에 작용하는 '시스템'이라 Entity 가 아니다.
# world 가 Environment 인스턴스를 하나 들고 매 프레임 update() 를 호출한다.
# =============================================================================
import random

from grassland.config import DAY_LENGTH_HOURS, GAME_HOURS_PER_SECOND


class Environment:
    """게임 내 시간·날씨·온도와 종료 여부를 관리."""
    def __init__(self):
        self.day = 1
        self.time = 6.0            # 6시=아침
        self.weather = "sunny"     # sunny / cloudy / rain / drought
        self.temperature = 28
        self.ended = False
        self.end_reason = ""

    def update(self, dt):
        """dt(초)만큼 시간 진행. 하루가 넘어가면 True 반환."""
        previous_day = self.day
        self.change_time(dt * GAME_HOURS_PER_SECOND)
        return self.day != previous_day

    def change_time(self, hours):
        self.time += hours
        while self.time >= DAY_LENGTH_HOURS:
            self.time -= DAY_LENGTH_HOURS
            self.change_day()

    def change_day(self):
        self.day += 1
        self.change_weather()
        self.change_temp()

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
