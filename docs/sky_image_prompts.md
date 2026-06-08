# 하늘 스프라이트(구름·해·달) 이미지 생성 요청서

이 문서는 ChatGPT(이미지 생성)에게 그대로 복사해 붙여넣어 사용할 수 있는
프롬프트 모음입니다. 게임 배경(`assets/sprites/background.png`)이
부드러운 그라데이션 하늘 + 사실적인 초원 일러스트 스타일이므로,
세 이미지 모두 **이 배경과 톤·질감이 어울리도록** 같은 스타일 키워드를
공유합니다.

공통 스타일 키워드(모든 프롬프트 끝에 동일하게 포함):
> soft painterly illustration, semi-realistic, warm natural lighting,
> matches a savanna grassland game background with a soft blue gradient
> sky, smooth shading, no harsh outlines, transparent background (PNG),
> game sprite asset, clean isolated object centered in frame

---

## 1. 구름 (Cloud)

**파일명 제안**: `cloud.png`
**용도**: 하늘 띠를 가로로 흘러가는 구름. 가로로 긴 연기/안개 느낌.

### 프롬프트
```
A single horizontally elongated, wispy cloud shaped like soft drifting
smoke or mist, stretched wide and flat (landscape aspect ratio, about
3:1), with gently frayed, translucent edges that fade out — not a
puffy cumulus cloud. Pale white with soft warm-grey undertones,
semi-transparent so it feels light and airy. Soft painterly
illustration, semi-realistic, warm natural lighting, matches a savanna
grassland game background with a soft blue gradient sky, smooth
shading, no harsh outlines, transparent background (PNG), game sprite
asset, clean isolated object centered in frame.
```

### 체크포인트
- 배경이 반드시 투명(PNG, alpha) 이어야 합니다.
- 세로보다 가로로 훨씬 긴 비율(예: 480×160px 권장)
- 가장자리가 또렷한 윤곽선 없이 자연스럽게 사라지는 형태

---

## 2. 해 (Sun)

**파일명 제안**: `sun.png`
**용도**: 낮 시간대에 하늘을 가로질러 이동하는 해. 기존 모습(따뜻한 노란
원반 + 은은한 광륜)과 크게 다르지 않되, 배경 일러스트와 같은 톤으로.

### 프롬프트
```
A warm glowing sun for a savanna grassland game sky, depicted as a
soft circular disc in warm golden-yellow (#FFEC96) with a gentle
radiant glow/halo fading outward in soft warm orange-gold tones —
similar to a classic stylized game sun, not photorealistic, not
flaring rays. Smooth radial gradient, soft painterly illustration,
semi-realistic, warm natural lighting, matches a savanna grassland
game background with a soft blue gradient sky, smooth shading, no
harsh outlines, transparent background (PNG), game sprite asset,
clean isolated object centered in frame.
```

### 체크포인트
- 정사각형에 가까운 비율(예: 256×256px), 중앙에 원반
- 배경 투명, 가장자리는 은은한 글로우로 자연스럽게 페이드아웃
- 색감은 배경 그림의 따뜻한 햇살 톤과 어울리게 (너무 쨍한 흰색/주황 X)

---

## 3. 달 (Moon)

**파일명 제안**: `moon.png`
**용도**: 밤 시간대에 하늘을 가로지르는 달. 표면의 크레이터·음영이 잘
드러나야 함.

### 프롬프트
```
A softly glowing moon for a savanna grassland game night sky, depicted
as a pale bluish-white circular disc (#EEF2FF) with clearly visible
surface details — subtle craters, maria (dark patches), and soft
shadow gradients giving it a gentle 3D, textured look — surrounded by
a faint cool-toned glow/halo. Soft painterly illustration,
semi-realistic, gentle moonlight, matches a savanna grassland game
background with a soft blue gradient sky, smooth shading, no harsh
outlines, transparent background (PNG), game sprite asset, clean
isolated object centered in frame.
```

### 체크포인트
- 정사각형에 가까운 비율(예: 256×256px), 중앙에 원반
- 표면의 크레이터/음영이 또렷하게 보이되 과하게 사실적이지 않게(게임 톤 유지)
- 배경 투명, 은은한 차가운 톤의 글로우

---

## 적용 방법 메모 (참고용)

이미지를 받으면 `assets/sprites/` 아래 위 파일명으로 저장한 뒤,
`gui.py`의 `_make_cloud_surface`(절차적 구름 생성)와
`_draw_sun_or_moon`(절차적 해/달 원 그리기) 부분을 이미지 로드·블릿
방식으로 교체하면 됩니다 (기존 `get_sprite`/`get_background` 처럼
`grassland/sprites.py`에 로더를 추가하는 방식 권장).
