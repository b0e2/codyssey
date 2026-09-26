# GitGen

<p align="center">
  <b>Git 변경 사항으로 한국어 커밋 메시지와 Pull Request 초안을 만드는 CLI</b><br/>
  저장소 컨벤션, safe mode, 출력 검증을 적용하는 Python 기반 LLM 도구
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.9+" />
  <img src="https://img.shields.io/badge/interface-CLI-222222?style=flat-square" alt="CLI" />
  <img src="https://img.shields.io/badge/LLM-Chat%20Completions-7C3AED?style=flat-square" alt="Chat Completions" />
  <img src="https://img.shields.io/badge/testing-pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white" alt="pytest" />
</p>

---

## Overview

GitGen은 현재 Git 저장소의 브랜치, 상태와 staged/unstaged diff를 수집해 한국어 커밋 메시지와 Pull Request 초안을 만드는 Python CLI 도구입니다.

Chat Completions 호환 LLM API를 사용하며, 한 번 실행할 때 API를 한 번만 호출합니다. 모델 응답은 저장소 컨벤션과 로컬 검증을 통과한 뒤 초안으로 출력됩니다.

## Problem

- 변경 범위가 커지면 핵심을 반영한 커밋 메시지를 일관되게 작성하기 어려움
- 저장소마다 허용하는 prefix, 제목 길이와 PR 섹션이 다름
- diff에 API Key, 이메일과 같은 민감정보가 포함될 수 있음
- 모델 응답이 지정한 형식이나 언어를 따르지 않을 수 있음
- 초안 생성 과정에서 불필요한 API 재호출을 피해야 함

## Solution

- Git 상태와 diff를 하나의 컨텍스트로 수집
- YAML 설정으로 커밋과 PR 컨벤션 분리
- safe mode에서 파일 제외, 민감값 마스킹과 크기 제한 적용
- strict JSON Schema와 로컬 후처리로 출력 형식 검증
- 명령 한 번당 LLM API 요청을 한 번으로 제한

## Core Features

- `commit`: Conventional Commit prefix가 포함된 커밋 메시지 생성
- `pr`: `Why`, `What`, `How to Test` 섹션이 있는 PR 초안 생성
- staged와 unstaged 변경을 함께 수집
- 민감정보 마스킹과 diff 크기 제한을 적용하는 safe mode
- YAML 파일을 이용한 prefix, 제목 길이, PR 섹션 설정
- strict JSON Schema 응답과 로컬 출력 검증
- 인증, 요청 한도, 네트워크, 잘못된 응답 오류 구분

## 요구 환경

- Python 3.9 이상
- Git
- LLM API Key와 Chat Completions endpoint

## 설치

```bash
git clone https://github.com/b0e2/codyssey.git
cd codyssey/b3/b3-2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

설치 확인:

```bash
git-gen --help
pytest -q
```

## LLM API 설정

예시 파일을 복사합니다.

```bash
cp .env.example .env
```

`.env`에 발급받은 Key를 입력합니다.

```dotenv
LLM_API_KEY=YOUR_LLM_API_KEY
LLM_API_ENDPOINT=https://example.com/v1/chat/completions
```

`LLM_API_ENDPOINT`에는 사용하는 LLM API의 Chat Completions endpoint를 입력합니다. CLI는 `.env`를 자동으로 읽지 않으므로 실행할 터미널에 환경변수를 불러옵니다.

```bash
set -a
source .env
set +a
```

`.env`는 `.gitignore`에 포함되어 있습니다. API Key를 코드, 커밋, PR 본문에 작성하지 않습니다.

## 빠른 시작

변경 사항이 있는 Git 저장소의 루트에서 실행합니다.

```bash
git-gen commit
git-gen pr
```

모듈 방식도 지원합니다.

```bash
python -m git_gen commit
python -m git_gen pr
```

변경 사항이 없으면 API를 호출하지 않고 종료합니다.

```text
[INFO] 변경 사항이 없습니다. 생성을 종료합니다.
```

## 실행 옵션

```text
--model MODEL
--temperature TEMPERATURE
--max-tokens MAX_TOKENS
--safe-mode / --no-safe-mode
--convention CONVENTION
```

| 항목 | 기본값 | 설명 |
| --- | --- | --- |
| 모델 | `openai/gpt-oss-20b` | 기본 생성 모델, `--model`로 변경 |
| temperature | `0.2` | `0` 이상 `2` 이하 |
| commit max tokens | `800` | `--max-tokens`로 변경 |
| PR max tokens | `1500` | `--max-tokens`로 변경 |
| safe mode | 활성화 | `--no-safe-mode`로 비활성화 |
| 컨벤션 파일 | `.git-gen.yml` | `--convention`으로 다른 파일 선택 |

예시:

```bash
git-gen commit \
  --model openai/gpt-oss-20b \
  --temperature 0.1 \
  --max-tokens 1000 \
  --convention .git-gen.yml
```

## 컨벤션 설정

기본 `.git-gen.yml`:

```yaml
commit:
  title_max_length: 72
  prefixes:
    - feat
    - fix
    - docs
    - refactor
    - test
    - chore

pull_request:
  title_max_length: 80
  sections:
    - Why
    - What
    - How to Test

safe_mode:
  max_files: 10
  max_lines: 200
  mask_email: true
  exclude_files:
    - ".env"
    - "*.pem"
    - "*.key"
```

다른 규칙을 시험하려면 파일을 복사한 뒤 경로를 지정합니다.

```bash
cp .git-gen.yml team-convention.yml
git-gen commit --convention team-convention.yml
git-gen pr --convention team-convention.yml
```

생성 결과가 설정을 어기면 로컬 후처리와 검증을 적용합니다. 제목은 설정 길이로 자르고, 허용되지 않은 커밋 prefix와 비어 있는 PR 섹션은 오류로 처리합니다. 이 과정에서 API를 추가 호출하지 않습니다.

### 설정을 바꿀 때의 출력 차이

같은 변경에 서로 다른 설정 파일을 적용한 결과입니다. 대상은 `b0e2/imac-init` 저장소의 Finder 설정 단계 추가 변경입니다.

기본 `.git-gen.yml`(PR 섹션 `Why`, `What`, `How to Test`):

```text
--- PR Title ---
Finder 기본 설정 추가: 숨김 파일·확장자 표시 및 목록 보기 설정

--- PR Body ---
## Why
- Finder 설정을 스크립트에 포함시켜 초기 세팅을 완전하게 함

## What
- README에 Finder 설정 항목 추가 및 setup.sh에 Finder 설정 단계 추가

## How to Test
- setup.sh 실행 후 Finder에서 숨김 파일·확장자 표시 여부, 경로·상태 막대 표시, 목록 보기 설정을 확인
```

대상 저장소 스타일에 맞춘 설정(`init` prefix 허용, 커밋 제목 60자, PR 섹션 `배경`, `변경 사항`, `검증 방법`):

```yaml
commit:
  title_max_length: 60
  prefixes:
    - init
    - feat
    - fix
    - docs
    - refactor
    - chore

pull_request:
  title_max_length: 70
  sections:
    - 배경
    - 변경 사항
    - 검증 방법
```

```text
--- PR Title ---
Finder 기본 설정 추가 및 README 업데이트

--- PR Body ---
## 배경
- Finder 기본 설정을 스크립트에 포함시켜 개발 환경 초기화 시 일관성 확보 및 사용 편의성 향상

## 변경 사항
- README에 Finder 설정 항목을 추가했습니다
- setup.sh에 Finder 설정 단계(step_setup_finder)를 추가하고 STEP_NAMES 및 STEP_FUNCS 배열에 반영했습니다

## 검증 방법
- setup.sh를 실행한 뒤 Finder에서 숨김 파일·전체 확장자 표시, 경로·상태 막대 표시, 목록 보기가 적용되었는지 확인합니다
```

섹션 이름, 제목 길이, 허용 prefix는 설정 파일에서 결정되므로 코드 수정 없이 저장소별 규칙을 적용할 수 있습니다.

## safe mode

safe mode는 기본으로 활성화되며 API 요청 전에 다음 처리를 수행합니다.

1. `.env`, `*.pem`, `*.key` 등 설정된 파일의 diff 제외
2. API Key, token, secret, password 형태의 값 마스킹
3. 이메일 주소 마스킹
4. 최대 10개 파일, 200줄로 diff 제한

마스킹 값은 `[MASKED_API_KEY]`, `[MASKED_TOKEN]`, `[MASKED_SECRET]`, `[MASKED_EMAIL]`로 치환됩니다. 제외 패턴과 제한은 컨벤션 파일에서 변경할 수 있습니다.

```bash
git-gen commit --safe-mode
```

`--no-safe-mode`는 원본 diff를 그대로 전송할 수 있으므로 민감정보가 없음을 직접 확인한 경우에만 사용합니다.

### 적용 전후 비교

민감값이 들어간 변경을 두 설정으로 실행한 결과입니다.

수집된 원본 diff:

```diff
+API_KEY = "sk-live-abcdefghijklmnopqrstuvwxyz01"
+CONTACT_EMAIL = "someone@example.com"
+DB_PASSWORD = "super-secret-value"
```

`--safe-mode`로 전송되는 diff:

```diff
+API_KEY = "[MASKED_SECRET]"
+CONTACT_EMAIL = "[MASKED_EMAIL]"
+DB_PASSWORD = "[MASKED_SECRET]"
```

실행 로그도 달라집니다.

```text
$ git-gen commit --safe-mode
[INFO] Git diff 수집 완료: 9줄
[INFO] safe mode 적용 완료: 1개 파일, 9줄, 3건 마스킹

$ git-gen commit --no-safe-mode
[INFO] Git diff 수집 완료: 9줄
[WARN] safe mode가 비활성화되었습니다.
```

두 경우 모두 생성된 커밋 메시지는 같은 내용이었고, 차이는 전송되는 diff에만 있었습니다. 마스킹 대상은 값 부분이므로 변수명과 구조는 그대로 남습니다.

## 입출력 예시

예시 변경:

```diff
-def format_title(title):
-    return title
+def format_title(title, max_length=72):
+    return title[:max_length]
```

커밋 메시지:

```text
$ git-gen commit
[INFO] 현재 브랜치: feature/output-validation
[INFO] Git status 수집 완료: 3개 파일 변경 감지
[INFO] Git diff 수집 완료: 200줄
[INFO] safe mode 적용 완료: 3개 파일, 200줄, 0건 마스킹
[INFO] LLM API 요청 중... (1/1)
[INFO] API 호출 횟수: 1
[DONE] commit 초안 생성 완료

--- Commit Message ---
feat: 생성 결과 제목 길이 검증 추가

- 커밋 및 PR 제목 길이 제한 적용
- 컨벤션 설정 기반 출력 검증 추가
----------------------
```

PR 초안:

```text
$ git-gen pr
[INFO] 현재 브랜치: feature/output-validation
[INFO] Git status 수집 완료: 3개 파일 변경 감지
[INFO] Git diff 수집 완료: 200줄
[INFO] safe mode 적용 완료: 3개 파일, 200줄, 0건 마스킹
[INFO] LLM API 요청 중... (1/1)
[INFO] API 호출 횟수: 1
[DONE] pr 초안 생성 완료

--- PR Title ---
생성 결과 검증 및 컨벤션 적용

--- PR Body ---
## Why
- 생성 결과가 팀 규칙을 안정적으로 따르도록 검증 필요

## What
- 제목 길이와 커밋 prefix 검증 추가
- PR 필수 섹션과 불릿 형식 적용

## How to Test
- pytest 실행
----------------
```

생성 결과는 초안입니다. 내용을 검토한 뒤 `git commit` 또는 GitHub PR 작성에 사용합니다.

## 다른 저장소에 적용한 사례

`b0e2/imac-init` 저장소에 Finder 기본값 설정 단계를 추가하면서 이 도구로 커밋 메시지 1회와 PR 초안 1회를 생성했습니다.

- PR: https://github.com/b0e2/imac-init/pull/1
- 사용한 명령: `git-gen commit --convention imac-init.yml`, `git-gen pr --convention imac-init.yml`

초안과 최종 PR의 차이는 다음과 같습니다.

- 커밋 제목은 초안의 `feat: Finder 설정 추가`를 그대로 사용했습니다.
- PR 제목은 커밋 제목과 형식을 맞추기 위해 `feat:` prefix를 붙였습니다.
- 배경은 초안의 일반적인 표현 대신 반복 작업을 줄이려는 실제 이유로 바꿨습니다.
- 변경 사항은 파일별로 나누고 추가한 설정 항목을 명시했습니다.
- 검증 방법은 초안의 수동 확인 항목에 실제로 실행한 `bash -n setup.sh`, `--list`, `--dry-run --only finder`를 추가했습니다.
- 초안의 문장형 서술은 저장소 문서 톤에 맞춰 간단한 명사형으로 정리했습니다.

## 처리 흐름

```text
현재 Git 저장소
  -> 저장소 루트와 변경 상태 확인
  -> staged/unstaged diff 수집
  -> safe mode 마스킹과 크기 제한
  -> 명령별 프롬프트와 JSON Schema 구성
  -> LLM API 1회 호출
  -> 제목, prefix, 섹션, 불릿 검증
  -> 터미널에 초안 출력
```

코드는 역할별로 나뉩니다.

- `git.py`: Git 저장소 검증과 변경 정보 수집
- `generator.py`: safe mode, 프롬프트, schema, 출력 검증
- `llm_client.py`: LLM 요청과 응답 및 오류 처리
- `cli.py`: 옵션 파싱과 전체 실행 흐름

## 오류와 해결 방법

| 메시지 또는 상황 | 원인 | 해결 방법 |
| --- | --- | --- |
| `requires a different Python` | Python 3.8 이하 사용 | Python 3.9 이상으로 가상환경을 다시 생성 |
| `No module named git_gen` | 현재 Python 환경에 패키지가 설치되지 않음 | 가상환경을 활성화하고 `python -m pip install -e ".[dev]"` 실행 |
| `현재 위치는 Git 저장소가 아닙니다` | Git 저장소 밖에서 실행 | 저장소로 이동한 뒤 실행 |
| `프로젝트 루트에서 실행해 주세요` | 하위 디렉터리에서 실행 | 안내된 저장소 루트로 이동 |
| `LLM_API_KEY 환경변수가 설정되지 않았습니다` | Key 미설정 | `.env`를 작성하고 현재 셸에 로드 |
| `LLM_API_ENDPOINT 환경변수가 설정되지 않았습니다` | endpoint 미설정 | 사용하는 LLM API의 endpoint 입력 |
| `LLM API 인증에 실패했습니다` | 잘못되거나 만료된 Key | 사용 중인 LLM API 서비스에서 Key 확인 또는 재발급 |
| `LLM API 요청 한도를 초과했습니다` | HTTP 429 | 잠시 후 다시 실행 |
| `LLM API 네트워크 오류` | 연결 실패 또는 timeout | 네트워크 확인 후 재실행 |
| `LLM API 요청 실패 (HTTP ...)` | 그 밖의 API 요청 오류 | HTTP 상태와 응답 메시지 확인 |
| `LLM API 응답 JSON 형식이 올바르지 않습니다` | 응답 구조 또는 JSON 오류 | 모델과 옵션 확인 후 재실행 |
| `컨벤션 설정 파일을 찾을 수 없습니다` | 잘못된 경로 | `--convention` 경로 확인 |
| `컨벤션 설정 파일 형식이 올바르지 않습니다` | YAML 문법 오류 | 들여쓰기와 자료형 확인 |
| `... 설정은 객체여야 합니다` | YAML 섹션 구조 오류 | 해당 섹션을 key-value 객체로 작성 |
| `commit.title_max_length가 ... 너무 짧습니다` | prefix와 설명을 담을 수 없는 길이 | 제목 제한을 늘림 |
| `커밋 title prefix가 허용 목록에 없습니다` | 모델 결과가 prefix 규칙 위반 | prefix 설정 확인 후 재실행 |
| `커밋 title의 설명은 한국어로 작성해야 합니다` | 한국어 제목 대체 불가 | diff 내용을 확인하거나 재실행 |
| `PR title은 한국어로 작성해야 합니다` | 한국어 제목 대체 불가 | diff 내용을 확인하거나 재실행 |
| `생성 결과의 ... 형식이 올바르지 않습니다` | 필수 필드 또는 목록 형식 오류 | 다시 실행하거나 모델 변경 |

## 테스트

```bash
pytest -q
python -m compileall -q src tests
git diff --check
```

테스트는 Git 수집, safe mode, API 요청/오류 분류, 출력 형식, 컨벤션 적용, CLI 1회 호출을 포함합니다.

## 설계 원칙

- API Key는 환경변수로만 전달
- 애플리케이션 로그에 API Key를 출력하지 않음
- 명령 한 번에 API 요청 한 번
- 모델 출력은 strict JSON Schema와 로컬 검증을 모두 통과해야 함
- 프롬프트 속 diff는 명령이 아니라 데이터로 취급
- LLM 연동 코드는 클라이언트 모듈에 격리
- 자동 실행보다 사람이 검토할 수 있는 초안 생성을 우선

## 제한 범위

- 커밋, push, PR 생성이나 merge를 자동으로 수행하지 않습니다.
- 저장소 루트에서만 실행할 수 있습니다.
- untracked 파일은 이름만 status에 포함되며 파일 내용은 diff에 포함되지 않습니다.
- binary diff와 Git이 제공하지 않는 파일 내용은 분석하지 못합니다.
- 생성 품질은 모델, diff 범위, 컨벤션 설정에 영향을 받습니다.
- safe mode는 일반적인 민감정보 패턴을 줄이기 위한 방어선이며 모든 형태를 보장하지 않습니다.
