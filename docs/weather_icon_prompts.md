# 날씨 아이콘 이미지 생성 요청서

시뮬레이션에 등장하는 날씨는 `config.py`의 `WEATHER_TINT`에 정의된 4종류입니다:
**sunny(맑음) · cloudy(흐림) · rain(비) · drought(가뭄)**.

아래 프롬프트를 ChatGPT(이미지 생성)에 그대로 복사해 사용하세요.
배경 그림·하늘 스프라이트(`docs/sky_image_prompts.md`)와 톤이 어울리도록
공통 스타일 키워드를 모든 프롬프트에 포함했습니다.

공통 스타일 키워드:
> flat minimal weather icon, simple rounded shapes, soft pastel colors,
> gentle painterly shading (not glossy/3D), warm friendly game-UI style
> matching a savanna grassland simulation, transparent background (PNG),
> clean isolated icon centered in frame, no text or labels

권장 크기: 64×64 ~ 128×128px, 정사각형, 배경 투명(PNG, alpha)

---

## 1. 맑음 (sunny)

**파일명 제안**: `weather_sunny.png`

```
A small flat-style weather icon of a bright sun: a warm golden-yellow
circle with a few short simple rays radiating outward, soft rounded
edges, gentle warm glow. Flat minimal weather icon, simple rounded
shapes, soft pastel colors, gentle painterly shading (not glossy/3D),
warm friendly game-UI style matching a savanna grassland simulation,
transparent background (PNG), clean isolated icon centered in frame,
no text or labels.
```

---

## 2. 흐림 (cloudy)

**파일명 제안**: `weather_cloudy.png`

```
A small flat-style weather icon of an overcast sky: one or two soft
puffy grey-white clouds overlapping, with a tiny hint of a pale sun
peeking behind them, muted cool-grey tones. Flat minimal weather icon,
simple rounded shapes, soft pastel colors, gentle painterly shading
(not glossy/3D), warm friendly game-UI style matching a savanna
grassland simulation, transparent background (PNG), clean isolated
icon centered in frame, no text or labels.
```

---

## 3. 비 (rain)

**파일명 제안**: `weather_rain.png`

```
A small flat-style weather icon of rain: a soft grey-blue puffy cloud
with three or four simple rounded raindrop shapes falling beneath it
in cool blue tones, gentle and friendly (not stormy or dark). Flat
minimal weather icon, simple rounded shapes, soft pastel colors,
gentle painterly shading (not glossy/3D), warm friendly game-UI style
matching a savanna grassland simulation, transparent background (PNG),
clean isolated icon centered in frame, no text or labels.
```

---

## 4. 가뭄 (drought)

**파일명 제안**: `weather_drought.png`

```
A small flat-style weather icon representing drought: a bright orange-
toned sun glowing over a patch of cracked, dry earth (simple curved
crack lines on a sandy-brown ground shape), warm dusty color palette
conveying heat and dryness without looking scary. Flat minimal weather
icon, simple rounded shapes, soft pastel colors, gentle painterly
shading (not glossy/3D), warm friendly game-UI style matching a
savanna grassland simulation, transparent background (PNG), clean
isolated icon centered in frame, no text or labels.
```

---

## 적용 메모 (참고용)

이미지를 받으면 `assets/sprites/`에 위 파일명으로 저장한 뒤,
`sprites.py`의 `get_sky_image()`와 같은 방식으로 로더를 추가하고,
`gui.py`의 `draw_ui()`(좌하단 정보 패널, `Weather: {env.weather}` 표시 부분)
옆에 해당 아이콘을 작게 그려주면 날씨가 한눈에 보이게 됩니다.
