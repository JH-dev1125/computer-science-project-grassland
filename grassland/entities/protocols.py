# =============================================================================
# protocols.py — '덕 타이핑' 계약 정의 (역할: 상호작용의 규칙)
#
# [덕 타이핑(duck typing)] "오리처럼 걷고 울면 오리다" — 어떤 클래스를 상속했느냐가 아니라
#   '특정 메서드를 가졌느냐'로 사용 가능 여부를 정하는 방식. 동물의 eat()/drink() 는 상대가
#   풀이든 사체든 물이든 '먹을/마실 메서드'만 있으면 그대로 호출한다(아래 Protocol 로 명시).
# =============================================================================
# [문법] from __future__ import annotations : 타입 힌트를 늦게 평가(전방 참조 허용). 동작엔 영향 없음.
from __future__ import annotations

# [문법] Protocol : '이런 메서드를 가진 무엇'이라는 구조적 타입을 정의(상속 강제 없이 형태만 약속).
#        runtime_checkable : isinstance(x, Consumable) 처럼 실행 중에도 검사 가능하게 해 준다.
#        TYPE_CHECKING : 타입 검사 도구가 읽을 때만 True. 실제 실행 땐 False라 아래 import 가 안 돌아
#        '순환 import'(animal ↔ protocols 가 서로 부르는 문제)를 피한다.
from typing import Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from grassland.entities.animals.animal import Animal


@runtime_checkable
class Consumable(Protocol):
    """consume(amount) 을 통해 부분 섭취가 가능한 객체."""
    # [의미] 풀·덤불·나무·사체·물웅덩이처럼 '조금씩 소모되는' 것은 모두 이 형태를 만족한다.

    def consume(self, amount: float) -> float:
        """실제로 섭취된 양을 반환한다."""
        # [문법] ... (Ellipsis) : '본문 없음'을 뜻하는 자리표시. Protocol 은 형태만 정의하므로 비워 둔다.
        ...


@runtime_checkable
class Drinkable(Protocol):
    """동물이 음용할 수 있는 객체 (water puddle, lake 등)."""

    def reduce_thirst(self, animal: "Animal") -> None:
        """animal 의 thirst 를 감소시킨다."""
        ...
