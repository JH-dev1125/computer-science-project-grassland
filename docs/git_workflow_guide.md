# 협업 시 깃(Git) 트리가 꼬이지 않게 작업하는 법

여러 명이 같은 저장소에서 작업하다 보면 히스토리가 갈래갈래 갈라지고
충돌이 자꾸 나는 경우가 많습니다. 아래 원칙과 상황별 명령어만 따라가면
훨씬 깔끔하게 협업할 수 있습니다.

---

## 0. 가장 중요한 기본 원칙 3가지

1. **작업 시작 전엔 항상 최신화하기**
   ```bash
   git pull --rebase origin main
   ```
   `git pull`을 그냥 쓰면 매번 "merge commit"이 자동으로 생겨서 히스토리가
   복잡하게 갈라집니다. **`--rebase` 옵션을 붙이면** 내 작업이 항상
   "최신 코드 위에 깔끔하게 얹히는" 형태가 되어 트리가 일직선으로 유지됩니다.

   👉 매번 옵션 붙이기 귀찮다면, 한 번만 아래 명령으로 기본값으로 설정해두세요:
   ```bash
   git config --global pull.rebase true
   ```

2. **커밋은 작게, 자주, 기능 단위로**
   한 커밋에 너무 많은 변경을 몰아넣으면 충돌 범위가 커지고 해결이 어려워집니다.
   "이 함수 하나 고침", "이 이미지 추가" 처럼 작은 단위로 자주 커밋하세요.

3. **가능하면 브랜치를 나눠서 작업하기**
   같은 파일을 여러 명이 동시에 건드리는 게 충돌의 가장 큰 원인입니다.
   - P는 `feature/A-작업` 브랜치에서, Q는 `feature/B-작업` 브랜치에서 작업
   - 끝나면 PR(Pull Request)로 `main`에 합치기

---

## 1. "내 작업은 그대로 두고, 남이 올린 새 변경사항만 받고 싶을 때"

> 예) P가 A.py를 작업해서 push했고, 나(Q)는 B.py를 작업 중. 내 B.py 작업은
> 지키면서 P가 올린 A.py만 받고 싶다.

```bash
git pull --rebase origin main
```

- 커밋 안 한 변경사항(working tree)은 그대로 보존된 채, 원격의 새 커밋만
  받아옵니다.
- 만약 "커밋된" 내 작업이 있다면, 그 커밋들이 P의 새 커밋 "위로" 자동으로
  재배치됩니다 (히스토리가 갈라지지 않고 일직선 유지).

만약 아직 커밋하지 않은 변경이 있어서 `pull --rebase`가 막힌다면:
```bash
git stash              # 변경사항을 잠시 치워두기
git pull --rebase origin main
git stash pop          # 치워둔 변경사항 다시 꺼내기
```

---

## 2. "같은 파일을 같이 작업했는데, 한쪽 버전으로 정리하고 싶을 때"

> 예) P와 Q가 같이 A.py를 고쳤는데, P의 버전이 더 나아서 Q도 P 버전으로
> 맞추고 싶다.

### 2-1. 다른 파일은 그대로 두고, 그 파일만 상대방 버전으로 교체
```bash
git fetch origin
git checkout origin/main -- A.py
```
→ A.py만 원격(P가 올린) 버전으로 바뀌고, 내가 작업 중인 다른 파일들은
그대로 유지됩니다.

### 2-2. 이미 충돌(conflict)이 난 상태라면
```bash
git fetch origin
git rebase origin/main
```
충돌난 파일을 열면 아래처럼 표시됩니다:
```
<<<<<<< HEAD
(내 코드)
=======
(상대방 코드)
>>>>>>> origin/main
```
유지하고 싶은 쪽(P의 코드)만 남기고 표시(`<<<<<<<`, `=======`, `>>>>>>>`)를
지운 뒤:
```bash
git add A.py
git rebase --continue
```

### 2-3. 내 모든 변경/커밋을 버리고 원격 상태로 완전히 맞추고 싶을 때
```bash
git fetch origin
git reset --hard origin/main
```
⚠️ **이 명령은 되돌릴 수 없습니다.** 로컬의 커밋 안 된 변경과,
원격에 없는 내 커밋이 전부 사라집니다. 실행 전 정말 필요 없는지 꼭 확인하세요.

---

## 3. 그 외 트리가 꼬였을 때 — 응급 처치

### "rebase 하다가 뭔가 잘못된 것 같다"
```bash
git rebase --abort
```
→ rebase를 시작하기 전 상태로 완전히 되돌립니다. 일단 이걸로 빠져나온 뒤
다시 천천히 시도하세요.

### "도저히 모르겠다, 일단 내 작업을 안전하게 백업하고 새로 시작하고 싶다"
```bash
git branch backup-내작업        # 지금 상태를 브랜치로 복사해 백업
git fetch origin
git reset --hard origin/main    # 깨끗한 최신 상태로 리셋
```
나중에 백업 브랜치(`backup-내작업`)에서 필요한 커밋만 골라올 수 있습니다:
```bash
git cherry-pick <커밋 해시>
```

### "지금 상태가 어떤지부터 보고 싶다"
```bash
git status                          # 변경된 파일 확인
git log --oneline --graph --all -10 # 최근 히스토리를 그래프로 보기
```

---

## 한눈에 보는 요약표

| 상황 | 명령어 |
|---|---|
| 작업 시작 전 최신화 | `git pull --rebase origin main` |
| 내 변경 잠시 치워두기 / 복원 | `git stash` / `git stash pop` |
| 특정 파일만 원격 버전으로 교체 | `git checkout origin/main -- 파일명` |
| 충돌 해결 후 계속 진행 | `git add 파일명` → `git rebase --continue` |
| rebase 취소하고 원상복구 | `git rebase --abort` |
| 내 변경 다 버리고 원격으로 맞추기 (위험) | `git reset --hard origin/main` |
| 지금 상태 백업해두기 | `git branch backup-이름` |

---

**기억할 것 한 가지만 꼽으라면**:
> 작업 시작 전엔 `git pull --rebase`, merge commit은 되도록 피하기.

이것만 팀 전체가 지켜도 트리가 꼬이는 일은 80% 이상 줄어듭니다.
