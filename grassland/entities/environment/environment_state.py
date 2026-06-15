# (구) 위치 호환용 shim — 실제 Environment 는 grassland/environment.py 에 있다.
#
# [문법] shim(심) : 옛 코드가 'grassland.entities.environment.environment_state' 경로로
#        Environment 를 import 하던 시절과의 호환을 위해, 실제 클래스를 그 자리에서 다시
#        내보내 주는 얇은 중계 파일. 새 코드는 grassland/environment.py 를 직접 쓴다.
from grassland.environment import Environment

# [문법] __all__ : 'from 이 모듈 import *' 했을 때 공개할 이름 목록.
__all__ = ["Environment"]
