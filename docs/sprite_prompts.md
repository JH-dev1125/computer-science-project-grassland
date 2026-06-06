# 개체 이미지(스프라이트) 생성 가이드 & ChatGPT 프롬프트

이 문서는 게임에 들어갈 동물·식물·자원·지형 이미지를 ChatGPT(DALL·E) 로 만들고
바로 프로그램에 적용하기 위한 안내서다. florr.io 의 mob, PokéRogue 의 포켓몬처럼
**단순하지만 형태와 특징이 또렷한** 그림을 목표로 한다.

---

## 1. 적용 방법 (코드 수정 불필요)

1. 아래 프롬프트로 이미지를 만든다.
2. 배경을 투명(PNG)으로 만들어 `assets/sprites/mobs/` 폴더에 넣는다.
3. 파일 이름을 **아래 표의 이름 그대로(소문자)** 로 저장한다.
4. 게임을 다시 실행한다 → 자동으로 그림이 적용된다.

이미지가 없는 개체는 예전처럼 색 도형으로 그려지므로, 하나씩 채워 넣어도 된다.

> 게임 코드는 `<개체이름 소문자>.png` 를 찾는다. 예) `Bald_Eagle` → `bald_eagle.png`,
> `Acacia_Tree` → `acacia_tree.png`. 띄어쓰기는 없고 단어 사이는 `_` 다.

---

## 2. 공통 스타일 프롬프트 (모든 그림에 공통 적용)

ChatGPT 에 먼저 아래 '스타일 규칙'을 알려주고 시작하면 그림들의 톤이 통일된다.
영어로 넣는 편이 결과가 더 안정적이다.

```
STYLE GUIDE (apply to every image):
- Cute mascot style like florr.io mobs and PokéRogue creatures: very simple,
  rounded, instantly readable shapes.
- Top-down / slight 3/4 view so it reads well on a top-down map.
- Flat colors with soft cel-shading, one bold soft outline, no gradients-heavy realism.
- A single centered subject only. No background, no scenery, no ground shadow, no text.
- Transparent background (PNG with alpha), square 1:1 canvas, 1024x1024.
- Clear silhouette: the animal must be recognizable as a tiny icon.
```

> **투명 배경 팁:** 생성 후 배경이 흰색/체크무늬로 남으면 ChatGPT 에
> "make the background fully transparent PNG, remove any background" 라고 한 번 더 요청한다.

---

## 3. 개체별 프롬프트

각 블록은 '공통 스타일 + 개체 설명'이 합쳐진 **그대로 붙여넣어 쓰는** 프롬프트다.

### 동물 (Animals)

**lion.png — 사자**
```
Cute simple top-down mascot of a male LION for a grassland game, florr.io/PokéRogue
style. Golden-tan body, big round brown mane, small rounded ears, calm strong face.
Flat colors, soft cel-shading, one bold outline. Single centered subject, transparent
background, no shadow, no text, square 1024x1024 PNG.
```

**hyena.png — 하이에나**
```
Cute simple top-down mascot of a spotted HYENA, florr.io/PokéRogue style. Sandy-grey
fur with dark spots, sloped back, pointed ears, sly grin. Flat colors, soft cel-shading,
one bold outline. Single centered subject, transparent background, no shadow, no text,
square 1024x1024 PNG.
```

**bald_eagle.png — 대머리 독수리**
```
Cute simple top-down mascot of a BALD EAGLE seen slightly from above with wings spread,
florr.io/PokéRogue style. White head, hooked yellow beak, dark-brown body and wings.
Flat colors, soft cel-shading, one bold outline. Single centered subject, transparent
background, no shadow, no text, square 1024x1024 PNG.
```

**zebra.png — 얼룩말**
```
Cute simple top-down mascot of a ZEBRA, florr.io/PokéRogue style. White body with bold
black stripes, short stiff mane, alert face. Flat colors, soft cel-shading, one bold
outline. Single centered subject, transparent background, no shadow, no text, square
1024x1024 PNG.
```

**gazelle.png — 가젤**
```
Cute simple top-down mascot of a GAZELLE, florr.io/PokéRogue style. Slender tan body,
white belly, thin curved horns, big gentle eyes, light and quick look. Flat colors, soft
cel-shading, one bold outline. Single centered subject, transparent background, no shadow,
no text, square 1024x1024 PNG.
```

**elephant.png — 코끼리**
```
Cute simple top-down mascot of an AFRICAN ELEPHANT, florr.io/PokéRogue style. Big rounded
grey body, large ears, short trunk and small white tusks, sturdy and calm. Flat colors,
soft cel-shading, one bold outline. Single centered subject, transparent background, no
shadow, no text, square 1024x1024 PNG.
```

**meerkat.png — 미어캣**
```
Cute simple top-down mascot of a MEERKAT standing upright like a sentinel, florr.io/
PokéRogue style. Small slim light-brown body, dark eye patches, alert pose. Flat colors,
soft cel-shading, one bold outline. Single centered subject, transparent background, no
shadow, no text, square 1024x1024 PNG.
```

**warthog.png — 혹멧돼지**
```
Cute simple top-down mascot of a WARTHOG, florr.io/PokéRogue style. Stocky grey-brown
body, short bristly mane, two small curved tusks, flat snout. Flat colors, soft
cel-shading, one bold outline. Single centered subject, transparent background, no shadow,
no text, square 1024x1024 PNG.
```

### 식물 (Plants)

**grass.png — 풀**
```
Cute simple top-down icon of a small GRASS TUFT for a grassland game, florr.io/PokéRogue
style. A round cluster of bright green blades. Flat colors, soft cel-shading, one bold
outline. Single centered subject, transparent background, no shadow, no text, square
1024x1024 PNG.
```

**bush.png — 덤불**
```
Cute simple top-down icon of a rounded leafy BUSH, florr.io/PokéRogue style. Dense
dark-green foliage as a soft blob, a few small berries optional. Flat colors, soft
cel-shading, one bold outline. Single centered subject, transparent background, no shadow,
no text, square 1024x1024 PNG.
```

**acacia_tree.png — 아카시아 나무**
```
Cute simple top-down icon of an AFRICAN ACACIA TREE, florr.io/PokéRogue style. Flat wide
umbrella-shaped green canopy, thin brown trunk, seen mostly from above. Flat colors, soft
cel-shading, one bold outline. Single centered subject, transparent background, no shadow,
no text, square 1024x1024 PNG.
```

**baobab_tree.png — 바오밥 나무**
```
Cute simple top-down icon of a BAOBAB TREE, florr.io/PokéRogue style. Very thick stout
brown trunk, small spread of branches and sparse green leaves on top. Flat colors, soft
cel-shading, one bold outline. Single centered subject, transparent background, no shadow,
no text, square 1024x1024 PNG.
```

### 자원 (Resources)

**water_puddle.png — 물웅덩이**
```
Cute simple top-down icon of a small WATER PUDDLE, florr.io/PokéRogue style. An oval pool
of clear blue water with a lighter highlight. Flat colors, soft cel-shading, one bold
outline. Single centered subject, transparent background, no shadow, no text, square
1024x1024 PNG.
```

**carcass.png — 사체**
```
Cute simple top-down icon of an animal CARCASS / bones, florr.io/PokéRogue style. A few
clean white bones and a rib cage, not gory, cartoonish and harmless looking. Flat colors,
soft cel-shading, one bold outline. Single centered subject, transparent background, no
shadow, no text, square 1024x1024 PNG.
```

### 지형 (Terrain)

**lake_side.png — 호숫가**
```
Cute simple top-down icon of a LAKE / pond seen from above, florr.io/PokéRogue style. A
rounded blue water area with a soft sandy or green edge ring. Flat colors, soft
cel-shading, one bold outline. Single centered subject, transparent background, no shadow,
no text, square 1024x1024 PNG.
```

**cave.png — 동굴**
```
Cute simple top-down icon of a rocky CAVE entrance seen from above, florr.io/PokéRogue
style. A cluster of grey-brown rocks around a dark round opening. Flat colors, soft
cel-shading, one bold outline. Single centered subject, transparent background, no shadow,
no text, square 1024x1024 PNG.
```

---

## 4. 일관성을 위한 팁

- **한 번에 한 마리씩** 만들고, 다음 그림을 요청할 때 "same style as before(앞과 같은
  스타일)" 라고 덧붙이면 톤이 잘 맞는다.
- 동물끼리 **상대적 크기**는 신경 쓰지 않아도 된다. 게임이 각 개체의 `radius` 에 맞춰
  자동으로 크기를 조절한다(코끼리는 크게, 미어캣은 작게).
- 모든 그림을 **정사각형**으로 만들어야 찌그러지지 않는다(게임이 정사각형으로 맞춤).
- 배경이 투명하지 않으면 흰 네모가 그대로 보인다. 꼭 투명 PNG 로 저장할 것.

## 5. 파일 이름 빠른 참조표

| 분류 | 개체 | 파일 이름 |
|---|---|---|
| 동물 | 사자 | `lion.png` |
| 동물 | 하이에나 | `hyena.png` |
| 동물 | 대머리 독수리 | `bald_eagle.png` |
| 동물 | 얼룩말 | `zebra.png` |
| 동물 | 가젤 | `gazelle.png` |
| 동물 | 코끼리 | `elephant.png` |
| 동물 | 미어캣 | `meerkat.png` |
| 동물 | 혹멧돼지 | `warthog.png` |
| 식물 | 풀 | `grass.png` |
| 식물 | 덤불 | `bush.png` |
| 식물 | 아카시아 | `acacia_tree.png` |
| 식물 | 바오밥 | `baobab_tree.png` |
| 자원 | 물웅덩이 | `water_puddle.png` |
| 자원 | 사체 | `carcass.png` |
| 지형 | 호숫가 | `lake_side.png` |
| 지형 | 동굴 | `cave.png` |
