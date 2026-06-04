# =============================================================================
# app.py — 실행기 (역할: main.py 의 하위, 프로그램 시작 절차)
# 인자 파싱 → World 생성 → GUI 또는 headless 실행. 시뮬 규칙·그리기는 안 한다.
# =============================================================================
import argparse

from grassland.world import World


def run():
    parser = argparse.ArgumentParser(description="와글와글 초원 생태계 시뮬레이션")
    parser.add_argument("--headless-steps", type=int, default=0,
                        help="창 없이 지정 횟수만큼 시뮬레이션(테스트용)")
    args = parser.parse_args()

    world = World.seed_default()

    if args.headless_steps > 0:               # 창 없이 빠르게 검증
        for _ in range(args.headless_steps):
            world.update(1 / 30)
        c = world.counts_by_name()
        print(f"Day {world.environment.day} {world.environment.clock_text()} "
              f"weather={world.environment.weather} | animals={len(world.living_animals())} "
              f"plants={len(world.alive_plants())} resources={len(world.resources)} | {c}")
        return

    from grassland.gui import GrasslandApp   # pygame 은 창이 필요할 때만 import
    GrasslandApp(world).run()
