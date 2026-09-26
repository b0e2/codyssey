# Troubleshooting Log

이 문서는 Git 작업 중 발생할 수 있는 문제를 재현하고 해결한 과정을 기록한다. 각 기록은 상황, 참여자, 명령, 결과, 선택 이유와 협업 시 주의점을 포함한다.
amend, reset, revert는 최신 `origin/main`에서 만든 로컬 전용 브랜치를 만들어서 진행했다. 해당 브랜치는 원격에 push하지 않았으며, 공유 브랜치와 기존 커밋 히스토리는 변경하지 않았다.

---

## 시나리오 1: git commit --amend

### 참여자

- 실행 및 기록: 정빈 (jeongbeen, @b0e2)

### 상황

실습용 커밋을 만든 뒤 빠뜨린 한 줄과 커밋 메시지를 원격 공유 전에 함께 수정해야 하는 상황을 재현했다.

### 실행 명령

```bash
printf 'amend initial line\n' > troubleshooting-practice.txt
git add troubleshooting-practice.txt
git commit -m "practice: amend 대상 커밋 생성"
printf 'amend added line\n' >> troubleshooting-practice.txt
git add troubleshooting-practice.txt
git commit --amend -m "practice: amend로 최근 커밋 수정"
```

### 실행 전후 로그

실행 전:

```text
e8f0b86 practice: amend 대상 커밋 생성
277b14d Merge pull request #21 from gitflow-practice-team/feature/juseong-learning-notes
```

실행 후:

```text
1a4feda practice: amend로 최근 커밋 수정
277b14d Merge pull request #21 from gitflow-practice-team/feature/juseong-learning-notes
```

- 실행 전 커밋: `e8f0b86a54f1de429602db90c5eb92c2a7034fb6`
- 실행 후 커밋: `1a4fedae1100bbfaded117e868a0664f6ea21843`
- 실행 후 `git status --short`: 출력 없음

### 결과와 배운 점

기존 커밋에 내용이 추가되고 메시지도 수정됐지만, 기존 해시가 유지되는 것이 아니라 새로운 해시의 커밋으로 교체됐다. 따라서 amend는 아직 원격에 공유하지 않은 자신의 최근 커밋에서만 사용하는 것이 안전하다.

---

## 시나리오 2: git reset --soft HEAD~1

### 참여자

- 실행 및 기록: 엄태동 (taedong, @TaeDongUm)

### 상황

실습용 로컬 커밋을 취소하되 파일 변경과 staging 상태는 유지한 뒤 다시 커밋하는 상황을 재현했다.

### 실행 명령

```bash
printf 'reset target line\n' >> troubleshooting-practice.txt
git add troubleshooting-practice.txt
git commit -m "practice: reset 대상 커밋 생성"
git reset --soft HEAD~1
git status --short
git commit -m "practice: reset 후 변경 재커밋"
```

### 실행 전후 로그

reset 실행 전:

```text
f27fd6d practice: reset 대상 커밋 생성
1a4feda practice: amend로 최근 커밋 수정
```

reset 실행 직후:

```text
HEAD: 1a4fedae1100bbfaded117e868a0664f6ea21843
M  troubleshooting-practice.txt
```

다시 커밋한 후:

```text
7d519f7 practice: reset 후 변경 재커밋
1a4feda practice: amend로 최근 커밋 수정
```

- reset 대상 커밋: `f27fd6dea93b2390c1fbbcaecbd67870f6beab66`
- 재커밋: `7d519f78457de5670548c8c5553bf84b861abb48`

### 결과와 배운 점

`reset --soft` 후 HEAD만 이전 커밋으로 이동했고 변경 파일은 staging 영역에 그대로 남았다. 커밋 단위를 다시 구성할 때 유용하지만 히스토리를 이동시키므로, 이미 push한 공유 커밋에는 사용하지 않는다. `reset --hard`는 사용하지 않았다.

---

## 시나리오 3: git revert

### 참여자

- 실행 및 기록: 박세헌 (park, @codyjourney)

### 상황

이미 공유된 커밋을 취소해야 하는 상황을 가정해, 실습용 변경 커밋을 삭제하지 않고 반대 변경을 담은 새 커밋을 생성했다.

### 실행 명령

```bash
printf 'revert target line\n' >> troubleshooting-practice.txt
git add troubleshooting-practice.txt
git commit -m "practice: revert 대상 변경 추가"
git revert --no-edit 34f8045428856a684e97ee971e400c3c35a9a17e
```

### 실행 전후 로그

revert 실행 전:

```text
34f8045 practice: revert 대상 변경 추가
7d519f7 practice: reset 후 변경 재커밋
1a4feda practice: amend로 최근 커밋 수정
```

revert 실행 후:

```text
84490f1 Revert "practice: revert 대상 변경 추가"
34f8045 practice: revert 대상 변경 추가
7d519f7 practice: reset 후 변경 재커밋
1a4feda practice: amend로 최근 커밋 수정
```

- 되돌린 커밋: `34f8045428856a684e97ee971e400c3c35a9a17e`
- 되돌리기 커밋: `84490f1d5d9cbda326cf38d2d49eca9046b7fa2a`
- 실행 후 `git status --short`: 출력 없음

### 결과와 배운 점

대상 커밋과 되돌리기 커밋이 모두 로그에 남았고, 대상 커밋이 추가했던 `revert target line`만 파일에서 제거됐다. 기존 히스토리를 재작성하지 않으므로 이미 공유된 변경을 취소할 때는 reset보다 revert가 안전하다.

---

## 시나리오 4: git stash / git stash pop

### 참여자

- 실행 및 기록: 육민우, 이주성 (minwoo, juseong) (@FickleBoBo, @YiJuseong)

### 상황

`docs/troubleshooting-log.md` 초안을 작성하던 중, 아직 커밋하지 않은 변경을 보존한 채 `main`으로 이동해 최신 기준 상태를 확인해야 했다.

### 시도한 명령과 절차

```bash
git status --short
git stash push -m "practice: save troubleshooting draft"
git stash list
git switch main
git switch feature/minwoo-final-evidence, git switch feature/juseong-final-evidence
git stash pop
```

### 결과

- 커밋되지 않은 트러블슈팅 문서 변경이 stash에 임시 보관됐다.
- 작업 트리가 깨끗해져 다른 브랜치로 안전하게 이동할 수 있었다.
- 원래 feature 브랜치로 돌아와 `git stash pop`을 실행하자 변경 내용이 복원됐다.
- pop 이후 적용된 stash 항목은 목록에서 제거됐다.

실제 확인 결과는 다음과 같았다.

```text
stash@{0}: On feature/minwoo-final-evidence: practice: save troubleshooting draft
Dropped refs/stash@{0} (02ebc4130b998ccd8d63316c6b784492dbec7e48)
```

`git stash list`를 다시 실행했을 때 항목이 출력되지 않았고, `git status --short`에는 복원된 `docs/troubleshooting-log.md` 수정이 표시됐다.

### 왜 이 방법을 선택했는가

작업이 완성되지 않아 임시 커밋을 만들고 싶지 않았고, 현재 변경을 잃지 않은 채 다른 브랜치로 이동해야 했기 때문이다. stash는 커밋 히스토리에 불완전한 작업을 남기지 않고 작업 디렉터리를 잠시 비울 수 있다.

### 주의할 점

- untracked 파일까지 보관하려면 `git stash -u`를 사용한다.
- `git stash pop` 중 현재 브랜치의 변경과 겹치면 충돌이 발생할 수 있다.
- 중요한 작업은 stash에 장기간 방치하지 않고, 복원 후 정상 반영 여부를 확인한다.
- `git stash list`와 `git stash show -p`로 보관 내용을 확인한 뒤 복원한다.
