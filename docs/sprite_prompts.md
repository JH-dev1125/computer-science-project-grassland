# 개체 이미지(스프라이트) 생성 가이드 — 포켓몬풍 도트 버전

이 문서는 16개 개체 이미지를 **포켓몬(PokéRogue) 배틀 스프라이트 느낌의 도트(픽셀) 아트**로
통일해서 만들고, 바로 게임에 적용하기 위한 프롬프트 모음이다.
동물·식물·자원·지형 **전부 같은 그림체**여야 하고, **크기 비율은 현실을 반영**한다.

---

## 0. 가장 먼저 — 크기는 게임이 자동으로 맞춘다

DALL·E(ChatGPT)는 1024×1024 같은 고정 크기로만 그림을 내보내서, "파일 크기"로 실제
크기비를 만들 수 없다. 그래서 **각 개체의 화면 표시 크기는 내가 게임 코드(`config.py`의
`SPRITE_DISPLAY_SIZE`)에 현실적인 비율로 이미 넣어 뒀다.** 아래 표가 그 값이다.

| 개체 | 표시 크기(px) | 개체 | 표시 크기(px) |
|---|---|---|---|
| 미어캣 Meerkat | 38 | 풀 Grass | 44 |
| 혹멧돼지 Warthog | 58 | 덤불 Bush | 76 |
| 가젤 Gazelle | 60 | 아카시아 Acacia | 160 |
| 대머리독수리 Bald_Eagle | 66 | 바오밥 Baobab | 175 |
| 하이에나 Hyena | 64 | 물웅덩이 Water_Puddle | 90 |
| 얼룩말 Zebra | 70 | 사체 Carcass | 54 |
| 사자 Lion | 84 | 호숫가 Lake_Side | 230 |
| 코끼리 Elephant | 120 | 동굴 Cave | 130 |

→ 코끼리는 미어캣의 약 3배, 바오밥·호숫가가 가장 크게 보인다. **이미지는 그냥 각자
정사각형 안을 꽉 채워 그리면 되고, 크기 차이는 게임이 알아서 만든다.** 숫자가 마음에
안 들면 그 값만 바꾸면 된다.

**중요(도트 크기 통일):** 게임이 이미지를 위 크기로 줄이므로, **도트(픽셀 한 칸)가 화면에서
같은 크기로 보이려면, 각 그림의 "도트 격자 해상도"를 위 표의 표시 크기와 비슷하게** 잡아야
한다. 즉 미어캣은 약 40×40 도트, 코끼리는 약 120×120 도트, 바오밥은 약 175×175 도트처럼.
작은 동물은 도트 수를 적게, 큰 구조물은 많게 그리면 게임 안에서 픽셀 크기가 일정해 보인다.

---

## 1. 적용 방법

1. 아래 프롬프트로 16개를 만든다.
2. **배경 투명 PNG**로 저장해 `assets/sprites/mobs/` 폴더에 넣는다.
3. 파일 이름은 표 아래의 이름(소문자) 그대로.
4. 게임 재실행 → 자동 적용.

> 배경 투명이 안 되면, **배경을 순수 마젠타(#FF00FF) 단색**으로 깔아서 저장해 줘.
> 도트 아트는 경계가 또렷해서 내가 그 색만 깔끔하게 지워(누끼) 적용할 수 있어.
> (지난번처럼 회색 배경이면 내가 다시 지워줄 테니 그냥 보내도 돼.)

---

## 2. 공통 스타일 규칙 (먼저 ChatGPT에 알려주고 시작)

```
STYLE GUIDE — apply to EVERY image, keep them perfectly consistent:
- Pixel art / dot art in the style of Pokémon battle sprites (PokéRogue look).
- Front-facing 3/4 view (slightly from above), same view for every subject.
- Low-resolution pixel grid with VISIBLE square pixels, hard edges, NO anti-aliasing,
  NO smooth gradients, NO blur.
- Limited palette (about 8-16 colors per sprite), simple dithering for shading,
  a clean 1-pixel dark outline around the whole shape.
- One single subject, centered, filling most of the square frame.
- Transparent background (PNG with alpha). If transparency is impossible, use a flat
  solid pure magenta (#FF00FF) background with hard edges.
- No text, no drop shadow on the ground, no extra scenery.
- Cute, readable, game-mascot proportions (slightly chibi), consistent outline
  thickness and pixel size across all sprites.
```

> 두 번째 그림부터는 프롬프트 끝에
> **"exact same pixel-art style, palette, outline, pixel size and view as the previous image"**
> 를 붙이면 그림체가 흐트러지지 않는다. 한 번에 하나씩 만드는 걸 추천.

---

## 3. 개체별 프롬프트 (그대로 붙여넣기용)

각 블록은 '공통 스타일 + 개체 + 권장 도트 해상도'까지 포함한 완성 프롬프트다.

### 동물

**lion.png — 사자** (도트 ~84×84)
```
Pixel-art sprite, Pokémon battle-sprite style (PokéRogue look), front 3/4 view.
A male LION: golden-tan body, big round brown mane framing the face, small rounded ears,
calm confident eyes. Visible square pixels, ~84x84 pixel grid, limited palette, dithered
shading, clean 1px dark outline, no anti-aliasing. Single centered subject, transparent
background, no shadow, no text.
```

**hyena.png — 하이에나** (도트 ~64×64)
```
Pixel-art sprite, Pokémon battle-sprite style (PokéRogue look), front 3/4 view.
A spotted HYENA: sandy-grey fur with dark spots, sloped back, pointed ears, short dark
mane, sly grin. Visible square pixels, ~64x64 pixel grid, limited palette, dithered
shading, clean 1px dark outline, no anti-aliasing. Single centered subject, transparent
background, no shadow, no text.
```

**bald_eagle.png — 대머리독수리** (도트 ~66×66, 날개로 가로가 더 넓어도 됨)
```
Pixel-art sprite, Pokémon battle-sprite style (PokéRogue look), front 3/4 view, wings
spread wide. A BALD EAGLE: white feathered head, hooked yellow beak, dark-brown body and
wings, fierce eyes. Visible square pixels, ~66 px tall pixel grid (wider than tall is ok),
limited palette, dithered shading, clean 1px dark outline, no anti-aliasing. Single
centered subject, transparent background, no shadow, no text.
```

**zebra.png — 얼룩말** (도트 ~70×70)
```
Pixel-art sprite, Pokémon battle-sprite style (PokéRogue look), front 3/4 view.
A ZEBRA: white body with bold black stripes, short stiff upright mane, alert friendly
face. Visible square pixels, ~70x70 pixel grid, limited palette, dithered shading, clean
1px dark outline, no anti-aliasing. Single centered subject, transparent background, no
shadow, no text.
```

**gazelle.png — 가젤** (도트 ~60×60)
```
Pixel-art sprite, Pokémon battle-sprite style (PokéRogue look), front 3/4 view.
A GAZELLE: slender tan body, white belly, thin curved horns, big gentle eyes, light and
quick look. Visible square pixels, ~60x60 pixel grid, limited palette, dithered shading,
clean 1px dark outline, no anti-aliasing. Single centered subject, transparent background,
no shadow, no text.
```

**elephant.png — 코끼리** (도트 ~120×120, 가장 큰 동물)
```
Pixel-art sprite, Pokémon battle-sprite style (PokéRogue look), front 3/4 view.
A big AFRICAN ELEPHANT: large rounded grey body, big ears, short trunk, small white tusks,
sturdy calm look, clearly the largest animal. Visible square pixels, ~120x120 pixel grid,
limited palette, dithered shading, clean 1px dark outline, no anti-aliasing. Single
centered subject, transparent background, no shadow, no text.
```

**meerkat.png — 미어캣** (도트 ~38×38, 가장 작은 동물)
```
Pixel-art sprite, Pokémon battle-sprite style (PokéRogue look), front view.
A small MEERKAT standing upright like a sentinel: slim light-brown body, dark eye patches,
alert pose, clearly a tiny animal. Visible square pixels, ~38x38 pixel grid, limited
palette, dithered shading, clean 1px dark outline, no anti-aliasing. Single centered
subject, transparent background, no shadow, no text.
```

**warthog.png — 혹멧돼지** (도트 ~58×58)
```
Pixel-art sprite, Pokémon battle-sprite style (PokéRogue look), front 3/4 view.
A WARTHOG: stocky grey-brown body, short bristly mane, two small curved tusks, flat snout.
Visible square pixels, ~58x58 pixel grid, limited palette, dithered shading, clean 1px
dark outline, no anti-aliasing. Single centered subject, transparent background, no shadow,
no text.
```

### 식물

**grass.png — 풀** (도트 ~44×44, 작게)
```
Pixel-art tile, Pokémon-game style (PokéRogue look), top-down-ish view.
A small GRASS TUFT: a round cluster of bright green blades, simple. Visible square pixels,
~44x44 pixel grid, limited palette, dithered shading, clean 1px dark outline, no
anti-aliasing. Single centered subject, transparent background, no shadow, no text.
```

**bush.png — 덤불** (도트 ~76×76)
```
Pixel-art tile, Pokémon-game style (PokéRogue look), 3/4 view.
A rounded leafy BUSH: dense dark-green foliage as a soft round blob, a few small red
berries. Visible square pixels, ~76x76 pixel grid, limited palette, dithered shading,
clean 1px dark outline, no anti-aliasing. Single centered subject, transparent background,
no shadow, no text.
```

**acacia_tree.png — 아카시아 나무** (도트 ~160×160, 큼)
```
Pixel-art tile, Pokémon-game style (PokéRogue look), 3/4 view.
An AFRICAN ACACIA TREE: thin brown trunk, wide flat umbrella-shaped green canopy on top
(savanna look), clearly a large tree. Visible square pixels, ~160 px tall pixel grid
(wider than tall is ok), limited palette, dithered shading, clean 1px dark outline, no
anti-aliasing. Single centered subject, transparent background, no shadow, no text.
```

**baobab_tree.png — 바오밥 나무** (도트 ~175×175, 가장 큰 식물 — 모양 주의!)
```
Pixel-art tile, Pokémon-game style (PokéRogue look), 3/4 view.
A BAOBAB TREE in its iconic shape: one MASSIVE, smooth, swollen bottle-shaped brown trunk,
very thick and wide at the bottom, tapering up; on top only a SMALL sparse crown of bare
twiggy branches with a little green foliage (the famous 'upside-down tree' look). Grand and
ancient, clearly the biggest plant. Visible square pixels, ~175x175 pixel grid, limited
palette, dithered shading, clean 1px dark outline, no anti-aliasing. Single centered
subject, transparent background, no shadow, no text.
```

### 자원

**water_puddle.png — 물웅덩이** (도트 ~90×90)
```
Pixel-art tile, Pokémon-game style (PokéRogue look), top-down view.
A small WATER PUDDLE: an oval pool of clear blue water with a lighter highlight. Visible
square pixels, ~90 px wide pixel grid (wider than tall is ok), limited palette, dithered
shading, clean 1px dark outline, no anti-aliasing. Single centered subject, transparent
background, no shadow, no text.
```

**carcass.png — 사체** (도트 ~54×54)
```
Pixel-art tile, Pokémon-game style (PokéRogue look), top-down view.
An animal CARCASS: a few clean white bones and a small rib cage, cartoonish and harmless,
not gory. Visible square pixels, ~54x54 pixel grid, limited palette, dithered shading,
clean 1px dark outline, no anti-aliasing. Single centered subject, transparent background,
no shadow, no text.
```

### 지형

**lake_side.png — 호숫가** (도트 ~230×230, 가장 큼)
```
Pixel-art tile, Pokémon-game style (PokéRogue look), top-down view.
A LAKE / pond seen from above: a large rounded area of blue water with a soft sandy and
green grassy edge ring around it. Visible square pixels, ~230x230 pixel grid, limited
palette, dithered shading, clean 1px dark outline, no anti-aliasing. Single centered
subject, transparent background, no shadow, no text.
```

**cave.png — 동굴** (도트 ~130×130)
```
Pixel-art tile, Pokémon-game style (PokéRogue look), 3/4 view.
A rocky CAVE entrance: a mound of grey-brown rocks around a dark round opening. Visible
square pixels, ~130x130 pixel grid, limited palette, dithered shading, clean 1px dark
outline, no anti-aliasing. Single centered subject, transparent background, no shadow,
no text.
```

---

## 4. 파일 이름 빠른 참조

| 개체 | 파일 | 개체 | 파일 |
|---|---|---|---|
| 사자 | `lion.png` | 풀 | `grass.png` |
| 하이에나 | `hyena.png` | 덤불 | `bush.png` |
| 대머리독수리 | `bald_eagle.png` | 아카시아 | `acacia_tree.png` |
| 얼룩말 | `zebra.png` | 바오밥 | `baobab_tree.png` |
| 가젤 | `gazelle.png` | 물웅덩이 | `water_puddle.png` |
| 코끼리 | `elephant.png` | 사체 | `carcass.png` |
| 미어캣 | `meerkat.png` | 호숫가 | `lake_side.png` |
| 혹멧돼지 | `warthog.png` | 동굴 | `cave.png` |

## 5. 통일감 체크리스트

- [ ] 16개 모두 **같은 시점**(front 3/4)·**같은 외곽선 두께**·**같은 도트 크기 느낌**인가?
- [ ] 명암 처리(디더링)와 팔레트 톤이 서로 비슷한가?
- [ ] 배경이 투명(또는 순수 #FF00FF)인가?
- [ ] 바오밥은 '뚱뚱한 병 모양 줄기 + 작은 가지 머리'로 제대로 나왔는가?
- [ ] 큰 개체(코끼리·바오밥·호숫가)는 도트 수가 많고, 작은 개체(미어캣·풀)는 적은가?
