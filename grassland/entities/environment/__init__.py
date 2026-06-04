# (구) 위치 호환용 shim — 실제 정의는 grassland/environment.py 한 곳뿐이다.
# 이 폴더는 더 이상 쓰지 않으며, 프로세스 종료 후 삭제 권장.
from grassland.environment import Environment, DroughtEvent

__all__ = ["Environment", "DroughtEvent"]
