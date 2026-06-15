# (구) 위치 호환용 shim — 실제 정의는 grassland/environment.py 한 곳뿐이다.
# 이 폴더는 더 이상 쓰지 않으며, 프로세스 종료 후 삭제 권장.
# [문법] 옛 경로 'grassland.entities.environment' 로 Environment 를 import 하던 코드와의
#        호환을 위해, 실제 클래스를 여기서 다시 내보내 주는 중계(shim) 역할만 한다.
from grassland.environment import Environment, DroughtEvent

__all__ = ["Environment", "DroughtEvent"]
