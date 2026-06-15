# =============================================================================
# app.py — 실행기 (역할: main.py 의 하위, 프로그램 시작 절차)
# 인자 파싱 → World 생성 → GUI 또는 headless 실행. 시뮬 규칙·그리기는 안 한다.
# =============================================================================
#
#  [실행 흐름 위치]  main.py(run 호출)  ─►  ★ 여기(app.run) ★  ─►  gui.GrasslandApp.run()
#
#  이 파일이 하는 일은 딱 세 가지:
#    1) 명령줄 인자를 읽는다 (--headless-steps 가 있는지)
#    2) World 를 만든다 (맵 + 동·식물 배치)  → world.py 의 seed_default()
#    3) 모드를 고른다:  창 없는 빠른 검증(headless)  /  실제 창을 띄우는 GUI
# =============================================================================

# [문법] import argparse : 파이썬 표준 라이브러리. 명령줄 인자(예: --headless-steps 100)를
#        손쉽게 정의·파싱하게 해 준다.
import argparse

# [흐름 0] 이 import 가 실행되는 순간 world.py 파일 전체가 로드된다.
#          (world.py 가 또 config·physics·environment·entities 들을 import 하므로,
#           사실상 이 한 줄로 프로젝트의 대부분 모듈이 메모리에 올라온다.)
# [호출→] 결과적으로 grassland/world.py 의 클래스 World 를 쓸 수 있게 된다.
from grassland.world import World


def run():
    """프로그램의 실제 시작 함수. main.py 의 run() 이 이걸 가리킨다."""
    # [←호출] main.py(또는 __main__.py)의 `run()` 한 줄에서 호출된다.

    # ── 1) 명령줄 인자 파싱 ────────────────────────────────────────────────
    # [변수] parser : 인자 정의를 담는 도구 객체.
    parser = argparse.ArgumentParser(description="와글와글 초원 생태계 시뮬레이션")
    # [문법] add_argument : 받을 인자를 등록한다.
    #        type=int  → 입력을 정수로 변환,  default=0 → 안 주면 0.
    # [변수] --headless-steps : 0 보다 크면 '창 없이 그 횟수만큼만 시뮬레이션'(테스트용).
    parser.add_argument("--headless-steps", type=int, default=0,
                        help="창 없이 지정 횟수만큼 시뮬레이션(테스트용)")
    # [변수] args : 파싱 결과. args.headless_steps 로 위에서 정한 값을 꺼내 쓴다.
    #        (argparse 는 '--headless-steps' 의 하이픈을 밑줄로 바꿔 속성명을 만든다.)
    args = parser.parse_args()

    # ── 2) 월드(맵) 생성 ──────────────────────────────────────────────────
    # [흐름 2] 맵을 만들고 그 안에 사자·얼룩말·풀·동굴 등을 '랜덤 배치'한다.
    # [문법] World.seed_default() : @classmethod(클래스 메서드). 인스턴스 없이 클래스 이름으로
    #        바로 부르며, 내부에서 World() 를 만들어 초기 배치까지 끝낸 뒤 돌려준다(팩토리 패턴).
    # [호출→] grassland/world.py 의 World.seed_default()
    #         └ 그 안에서 seed_structures()→seed_grass()→seed_carcasses()→seed_animals() 순서로 진행
    # [변수] world : 시뮬레이션의 모든 상태(동물·식물·자원·지형·환경·물리)를 담은 핵심 객체.
    world = World.seed_default()

    # ── 3) 실행 모드 분기 ─────────────────────────────────────────────────
    if args.headless_steps > 0:               # 창 없이 빠르게 검증(밸런스 실험·테스트)
        # [흐름 3-A] headless 경로: 창을 띄우지 않고 시뮬레이션 로직만 빠르게 N번 돌린다.
        # [문법] for _ in range(N) : N 번 반복. 반복 변수를 안 쓸 때 관례적으로 이름을 _ 로 둔다.
        for _ in range(args.headless_steps):
            # [호출→] world.update(dt) : 시뮬레이션을 한 칸(dt초) 진행. dt 를 1/30 로 고정해
            #         '초당 30프레임'인 셈 치고 일정하게 돌린다.
            world.update(1 / 30)
        # [변수] c : 종(이름)별 살아있는 마리 수 딕셔너리. 결과 요약 출력에 쓴다.
        # [호출→] world.counts_by_name()
        c = world.counts_by_name()
        # [문법] f"...{식}..." : f-string. 문자열 안 {중괄호}에 변수·식을 그대로 끼워 넣는다.
        #        여러 줄에 걸친 f"..." f"..." 는 그냥 이어 붙여 한 문장으로 출력된다.
        print(f"Day {world.environment.day} {world.environment.clock_text()} "
              f"weather={world.environment.weather} | animals={len(world.living_animals())} "
              f"plants={len(world.alive_plants())} resources={len(world.resources)} | {c}")
        # [흐름 끝-A] headless 모드는 여기서 종료(return). 창을 열지 않는다.
        return

    # [흐름 3-B] GUI 경로(기본): 진짜 창을 열어 실시간으로 보여 준다.
    # [문법] 함수 '안'에서 import : pygame 은 창이 필요할 때만 불러오기 위해 여기서 늦게 import 한다
    #        (headless 모드에선 pygame 창이 필요 없으므로 불필요한 로딩을 피한다 — '지연 임포트').
    # [호출→] grassland/gui.py 의 GrasslandApp 클래스
    from grassland.gui import GrasslandApp
    # [흐름 4] GrasslandApp(world) 로 화면 앱 객체를 만들고(pygame 창 생성), .run() 으로
    #          '매 프레임 메인 루프'에 들어간다. 이 run() 은 창을 닫을 때까지 끝나지 않는다.
    # [호출→] gui.GrasslandApp.__init__()  그리고 이어서  gui.GrasslandApp.run()
    GrasslandApp(world).run()
