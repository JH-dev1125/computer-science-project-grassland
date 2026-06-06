이 폴더에 개체별 이미지(PNG)를 넣으면 게임이 자동으로 불러서 그립니다.

■ 파일 이름 규칙 (반드시 소문자, 띄어쓰기 대신 _)
  동물 : lion.png  hyena.png  bald_eagle.png  zebra.png
         gazelle.png  elephant.png  meerkat.png  warthog.png
  식물 : grass.png  bush.png  acacia_tree.png  baobab_tree.png
  자원 : water_puddle.png  carcass.png
  지형 : lake_side.png  cave.png
  (plain = 배경이라 이미지가 필요 없습니다)

■ 권장 형식
  - 정사각형(예: 512x512 또는 1024x1024)
  - 배경 투명(PNG, alpha)
  - 개체 하나만 중앙에, 그림자/글자 없음

■ 적용 방법
  파일을 이 폴더에 넣고 게임을 다시 실행하면 끝.
  이미지가 없는 개체는 예전처럼 색 도형으로 그려집니다(폴백).

자세한 ChatGPT 생성 프롬프트는 docs/sprite_prompts.md 를 보세요.
