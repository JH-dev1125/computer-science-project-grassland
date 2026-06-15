# grassland 패키지 루트
#
# [문법] __init__.py : 이 파일이 있으면 그 폴더가 '패키지'(import 가능한 모듈 묶음)가 된다.
#        'import grassland' 하면 이 파일이 가장 먼저 실행된다(여기선 거의 비어 있음).
# [문법] __all__ : 'from grassland import *' 했을 때 가져올 하위 모듈 이름 목록(문서화 의미도 있음).
__all__ = ["app", "world", "gui", "physics", "sprites", "environment", "config"]
