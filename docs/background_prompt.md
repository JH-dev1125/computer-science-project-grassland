# 초원 배경 텍스처 생성 가이드 & 프롬프트

게임 바닥(초원)에 깔 **배경 텍스처**를 만들기 위한 안내서다. 게임은 이 그림 한 장을
**가로·세로로 이어 붙여(타일링)** 넓은 초원을 채운다. 그래서 **이음매 없이 반복(seamless
tileable)** 되는 그림이어야 한다.

---

## 1. 적용 방법 (코드 수정 불필요)

1. 아래 프롬프트로 텍스처를 만든다.
2. `assets/sprites/background.png` 로 저장한다(이 경로·이름 그대로).
3. 게임을 다시 실행하면 바닥이 그 텍스처로 깔린다.
4. 파일이 없으면 예전처럼 단색 초록 배경이 쓰인다(폴백).

> 게임은 세로 고정·가로 스크롤이라, 텍스처는 가로로 흐르고 세로로는 반복돼 화면을 채운다.
> 권장 크기는 **512×512**(정사각형). 너무 작으면 반복이 티 나고, 너무 크면 무겁다.

---

## 2. 핵심 조건 — 반드시 지킬 것

```
- SEAMLESS / TILEABLE texture: the left edge must connect to the right edge, and the
  top edge to the bottom edge, with NO visible seam when repeated.
- Top-down view (seen straight from above), flat — this is a ground texture, not a scene.
- NO distinct objects (no single tree, rock, animal, pond, path) — those are separate
  sprites. Only ground.
- Even, uniform overall look so it can repeat many times without obvious patterns or a
  bright/dark corner.
- 512x512, square.
```

---

## 3. 프롬프트 (그대로 붙여넣기용)

기존 동물·식물 그림과 **같은 톤(밝은 만화풍 사바나)** 으로 맞춘 버전이다.

```
A seamless tileable top-down ground texture of African savanna grassland, cartoon game-art
style matching cute mobile games. Short green savanna grass with subtle patches of lighter
and darker green and a few tiny dry/yellow grass blades and small specks of soil for
variation. Flat, seen directly from above, soft cel-shading, no harsh shadows. Even and
uniform so it repeats cleanly. IMPORTANT: fully seamless and tileable on all four edges,
no visible seam, no single distinct objects (no trees, rocks, ponds, paths, or animals),
no text. 512x512, square.
```

### 색을 게임과 맞추고 싶다면
게임의 기본 초원색은 RGB **(126, 184, 92)** 근처다. 프롬프트에 한 줄 덧붙이면 톤이 맞는다:
```
Base grass color around RGB (126,184,92), a warm medium green.
```

---

## 4. (선택) "전체 맵 한 장" 방식

타일 대신 **아주 넓은 한 장**(가로로 긴 초원 전경)을 만들어 깔고 싶다면:
- 가로로 매우 긴 비율(예: 3840×570)로, 위쪽 일부는 비우고(하늘은 게임이 그림) 아래는 초원.
- 다만 이 경우 끝까지 스크롤하면 그림이 끝나므로, **타일 방식(위 3번)을 더 추천**한다.
- 원하면 내가 코드에서 "하늘 영역/초원 영역 분리"를 맞춰 줄 수 있으니 말해줘.

---

## 5. 체크리스트
- [ ] 네 변이 모두 이어지는가(좌↔우, 상↔하)? 반복해도 줄·격자무늬가 안 생기는가?
- [ ] 위에서 똑바로 내려다본 평평한 바닥인가(원근·그림자 없음)?
- [ ] 나무·바위·웅덩이 같은 '개체'가 안 들어갔는가?
- [ ] 전체적으로 고르게 밝아 한쪽 구석만 튀지 않는가?
- [ ] 파일명이 정확히 `background.png` 이고 `assets/sprites/` 에 있는가?
