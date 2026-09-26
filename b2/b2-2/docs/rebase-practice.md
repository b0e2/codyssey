# Interactive Rebase Practice

## 목적

개인 feature 브랜치에서 여러 문서 커밋을 `git rebase -i`로 정리하고, 정리 전후의 히스토리를 비교한다.

## 실습 브랜치

- `feature/jeongbeen-final-evidence`

## 실습 절차

1. 관련 내용을 세 개의 작은 커밋으로 나누어 작성한다.
2. 정리 전 `git log --oneline` 결과를 저장한다.
3. `git rebase -i HEAD~3`에서 두 커밋을 `squash`한다.
4. 최종 커밋 메시지를 작업 전체가 드러나도록 수정한다.
5. 정리 후 히스토리를 다시 확인한다.

## 안전 수칙

- `main`과 공유 브랜치에서는 히스토리를 재작성하지 않는다.
- 원격에 push하기 전의 개인 feature 브랜치에서만 수행한다.
- 이미 공유한 커밋을 rebase했다면 강제 push가 필요할 수 있으므로 팀 합의 없이 진행하지 않는다.
- 충돌이 발생하면 변경 목적을 확인하고 해결한 뒤 `git rebase --continue`를 사용한다.

## 정리 전 히스토리

```text
ae33ae6 docs: interactive rebase 안전 수칙 추가
2f24b9f docs: interactive rebase 실습 절차 추가
ca7ada6 docs: interactive rebase 실습 문서 초안 추가
```

세 커밋은 모두 같은 문서를 완성하기 위한 작은 변경이었기 때문에 하나의 작업 단위로 정리하기로 했다.

## 수행 명령

```bash
git rebase -i HEAD~3
```

대화형 편집 화면에서 첫 커밋은 `pick`으로 유지하고, 나머지 두 커밋은 `squash`로 변경했다. 최종 커밋 메시지는 작업 전체가 드러나도록 수정했다.

## 정리 후 히스토리

```text
b677adf docs: interactive rebase 실습 내용 정리
```

세 개의 커밋이 하나의 의미 있는 커밋으로 정리됐다. 이 작업은 원격에 push하기 전 개인 feature 브랜치에서 수행했으므로 다른 팀원의 작업 기준점에는 영향을 주지 않았다.

## 배운 점

interactive rebase는 관련 커밋을 정리해 히스토리를 읽기 쉽게 만들 수 있다. 반면 기존 커밋의 해시를 변경하므로, 이미 공유된 브랜치에서 실행하면 다른 팀원의 로컬 히스토리와 충돌할 수 있다. 따라서 팀 합의 없이 공유 브랜치에서 rebase하거나 강제 push하지 않는다.
