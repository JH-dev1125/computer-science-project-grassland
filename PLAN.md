# 아키텍처 분석 및 개선 계획

## 호출 흐름 아키텍처

```
app.run()
  │
  ├─ World.seed_default()
  │    ├─ World.__init__()          ← Environment, PhysicsEngine 초기화
  │    ├─ seed_terrain()            ← Plain / LakeSide / Cave
  │    ├─ seed_plants()             ← Grass×3 / Bush / AcaciaTree / BaobabTree
  │    └─ seed_resources()          ← WaterPuddle×2 / Carcass
  │
  └─ GrasslandApp(world).run()      ← pygame 게임 루프
       │
       ├─ [이벤트] quit / resize / drag
       │
       ├─ World.update(dt)
       │    ├─ Environment.update()       → 시간·날씨·온도 진행
       │    ├─ on_new_day()               → WaterPuddle.fill_rain()
       │    ├─ DroughtEvent.dry_up_map()  → [가뭄 시] WaterPuddle 소모
       │    ├─ Plant.update() ×N          → photosynthesize()
       │    ├─ Animal.update() ×N
       │    │    └─ behave(world, dt)     ← @abstractmethod 구현체
       │    │         ├─ Herbivore.behave()
       │    │         │    ├─ nearest_predator() → fight_or_flight() / hide_in_bush()
       │    │         │    ├─ seek_water()       → drink(Drinkable)
       │    │         │    ├─ seek_plants()      → eat(Consumable)
       │    │         │    └─ try_reproduce()    → spawn_offspring()
       │    │         ├─ Carnivore.behave()
       │    │         │    ├─ seek_water()
       │    │         │    ├─ nearest_carcass()  → eat(Carcass)
       │    │         │    └─ find_prey() → hunt() → attack()
       │    │         │                          → die() → spawn_carcass()
       │    │         └─ Omnivore.behave()
       │    │              ├─ nearest_predator() → flee_or_fight()
       │    │              ├─ seek_water()
       │    │              └─ decide_food()      → eat(Carcass | Plant)
       │    ├─ PhysicsEngine.update()    → _separate() + _integrate()
       │    └─ check_end_conditions()
       │
       └─ GrasslandApp.draw()
            ├─ draw_field()          ← 격자
            ├─ draw_terrains()       ← LakeSide / Cave
            ├─ draw_plants()
            ├─ draw_resources()      ← WaterPuddle / Carcass
            ├─ draw_animals()        ← 체력바 + action_text
            ├─ draw_sky_overlay()    ← 날씨별 하늘 스프라이트
            └─ draw_ui()             ← Day / Weather / 개체 수 HUD
```

---

## 개선 방향성 보고서

### 현재 상태 요약

3단계 리팩토링으로 가장 중요한 뼈대는 잡혔다. `Entity(ABC)` → `Animal`(`behave` abstractmethod) → `Herbivore/Carnivore/Omnivore` → 구체 종의 계층이 정립됐고, `Consumable`·`Drinkable` Protocol로 덕타이핑이 제거됐다. `world.py`의 `Basic*` 레거시도 완전히 소멸됐다. 그러나 아직 세 곳에 기술 부채가 남아 있다.

---

### 남은 문제 1 — `gui.py`의 타입 누수

`draw_animals()`가 여전히 `getattr(animal, "alive", True)`, `getattr(animal, "radius", 18)` 등 6곳에서 방어적 접근을 하고 있다. `world.animals`가 `list[Animal]`로 타입 보장된 지금은 전부 직접 속성 접근으로 교체 가능하다. 또한 렌더링이 `terrain.name == "Lake_Side"` 같은 이름 문자열로 분기하는데, `isinstance(terrain, LakeSide)` 방식으로 바꾸면 오타로 인한 렌더링 누락을 컴파일 타임에 잡을 수 있다.

**액션:** `gui.py` 전체를 타입 정비하고, 이름 분기를 `isinstance`로 교체.

---

### 남은 문제 2 — `physics.py`의 타입 부재

`PhysicsEngine.update(entities, dt)`가 완전 무타입이다. `getattr(entity, "alive", True)`, `getattr(entity, "solid", True)` 두 곳 모두 `Entity`가 이 속성을 보장하므로 제거 가능하다. 파라미터도 `list[Animal]`로 좁혀서 넘기고 있으므로 시그니처에 반영해야 한다.

**액션:** `physics.py`에 `from __future__ import annotations` + 전체 타입 어노테이션 추가, `getattr` 제거.

---

### 남은 문제 3 — `Environment`·`DroughtEvent`의 위치

두 클래스가 `world.py` 안에 방치되어 있다. `Environment`는 `entities/environment/environment_state.py`에 이미 다른 버전이 있어 혼란을 준다. `DroughtEvent`는 `entities/environment/__init__.py`가 임포트하려 했으나 파일이 없던 클래스다.

**액션:** `Environment`를 `entities/environment/environment.py`로 이동하고 `environment_state.py`의 중복 버전 제거. `DroughtEvent`도 같은 패키지로 이동. `world.py`는 임포트만 하도록 정리.

---

### 중기 개선 — 이벤트 시스템 도입

현재 `animal.die()` → `world.spawn_carcass()` 처럼 엔티티가 World를 직접 역참조한다. 개체 수가 늘어나면 이 결합이 테스트와 확장을 어렵게 한다. 간단한 이벤트 버스(`EventBus`)를 두고 `AnimalDied`, `PlantConsumed` 같은 이벤트를 발행하면 World가 구독해 처리하는 구조로 분리할 수 있다. World가 수백 개의 엔티티 상태를 직접 조회하는 `nearest_*` 쿼리들도 공간 분할(그리드 해시 또는 쿼드트리)로 O(N²) → O(N log N)으로 개선될 여지가 있다.

---

### 우선순위 요약

| 순서 | 작업 | 난이도 | 효과 |
|---|---|---|---|
| 1 | `gui.py` 타입 정비 + isinstance 렌더 | 낮음 | 안정성 |
| 2 | `physics.py` 타입 어노테이션 | 낮음 | 일관성 |
| 3 | `Environment`/`DroughtEvent` 이동 | 중간 | 구조 명확화 |
| 4 | 이벤트 버스 도입 | 높음 | 결합도 감소 |
| 5 | 공간 분할 쿼리 최적화 | 높음 | 성능 |
