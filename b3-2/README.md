# Git 커밋/PR 초안 생성기

Git 저장소의 브랜치, 상태, staged/unstaged diff를 수집해 한국어 커밋 메시지와 Pull Request 초안을 만드는 Python CLI 도구입니다. GroqCloud Chat Completions API를 사용하며, 한 번 실행할 때 API를 한 번만 호출합니다.

## 주요 기능

- `commit`: Conventional Commit prefix가 포함된 커밋 메시지 생성
- `pr`: `Why`, `What`, `How to Test` 섹션이 있는 PR 초안 생성
- staged와 unstaged 변경을 함께 수집
- 민감정보 마스킹과 diff 크기 제한을 적용하는 safe mode
- YAML 파일을 이용한 prefix, 제목 길이, PR 섹션 설정
- strict JSON Schema 응답과 로컬 출력 검증
- 인증, 요청 한도, 네트워크, 잘못된 응답 오류 구분

## 요구 환경

- Python 3.10 이상
- Git
- GroqCloud API Key

## 설치

```bash
git clone https://github.com/b0e2/b3-2.git
cd b3-2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

설치 확인:

```bash
ai-gitgen --help
pytest -q
```

## API Key 설정

예시 파일을 복사합니다.

```bash
cp .env.example .env
```

`.env`에 발급받은 Key를 입력합니다.

```dotenv
AI_API_KEY=YOUR_GROQ_API_KEY
```

CLI는 `.env`를 자동으로 읽지 않으므로 실행할 터미널에 환경변수를 불러옵니다.

```bash
set -a
source .env
set +a
```

`.env`는 `.gitignore`에 포함되어 있습니다. API Key를 코드, 커밋, PR 본문에 작성하지 않습니다.

## 빠른 시작

변경 사항이 있는 Git 저장소의 루트에서 실행합니다.

```bash
ai-gitgen commit
ai-gitgen pr
```

모듈 방식도 지원합니다.

```bash
python -m ai_gitgen commit
python -m ai_gitgen pr
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
| 모델 | `openai/gpt-oss-20b` | 기본 생성 모델 |
| 품질 우선 모델 | `openai/gpt-oss-120b` | 필요할 때 `--model`로 선택 |
| temperature | `0.2` | `0` 이상 `2` 이하 |
| commit max tokens | `800` | `--max-tokens`로 변경 |
| PR max tokens | `1500` | `--max-tokens`로 변경 |
| safe mode | 활성화 | `--no-safe-mode`로 비활성화 |
| 컨벤션 파일 | `.ai-gitgen.yml` | `--convention`으로 다른 파일 선택 |

예시:

```bash
ai-gitgen commit \
  --model openai/gpt-oss-120b \
  --temperature 0.1 \
  --max-tokens 1000 \
  --convention .ai-gitgen.yml
```

## 컨벤션 설정

기본 `.ai-gitgen.yml`:

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
cp .ai-gitgen.yml team-convention.yml
ai-gitgen commit --convention team-convention.yml
ai-gitgen pr --convention team-convention.yml
```

생성 결과가 설정을 어기면 로컬 후처리와 검증을 적용합니다. 제목은 설정 길이로 자르고, 허용되지 않은 커밋 prefix와 비어 있는 PR 섹션은 오류로 처리합니다. 이 과정에서 API를 추가 호출하지 않습니다.

## safe mode

safe mode는 기본으로 활성화되며 API 요청 전에 다음 처리를 수행합니다.

1. `.env`, `*.pem`, `*.key` 등 설정된 파일의 diff 제외
2. API Key, token, secret, password 형태의 값 마스킹
3. 이메일 주소 마스킹
4. 최대 10개 파일, 200줄로 diff 제한

마스킹 값은 `[MASKED_API_KEY]`, `[MASKED_TOKEN]`, `[MASKED_SECRET]`, `[MASKED_EMAIL]`로 치환됩니다. 제외 패턴과 제한은 컨벤션 파일에서 변경할 수 있습니다.

```bash
ai-gitgen commit --safe-mode
```

`--no-safe-mode`는 원본 diff를 그대로 전송할 수 있으므로 민감정보가 없음을 직접 확인한 경우에만 사용합니다.

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
$ ai-gitgen commit
[INFO] 현재 브랜치: feature/output-validation
[INFO] Git status 수집 완료: 3개 파일 변경 감지
[INFO] Git diff 수집 완료: 200줄
[INFO] safe mode 적용 완료: 3개 파일, 200줄, 0건 마스킹
[INFO] AI API 요청 중... (1/1)
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
$ ai-gitgen pr
[INFO] 현재 브랜치: feature/output-validation
[INFO] Git status 수집 완료: 3개 파일 변경 감지
[INFO] Git diff 수집 완료: 200줄
[INFO] safe mode 적용 완료: 3개 파일, 200줄, 0건 마스킹
[INFO] AI API 요청 중... (1/1)
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

## 처리 흐름

```text
현재 Git 저장소
  -> 저장소 루트와 변경 상태 확인
  -> staged/unstaged diff 수집
  -> safe mode 마스킹과 크기 제한
  -> 명령별 프롬프트와 JSON Schema 구성
  -> GroqCloud API 1회 호출
  -> 제목, prefix, 섹션, 불릿 검증
  -> 터미널에 초안 출력
```

코드는 역할별로 나뉩니다.

- `git.py`: Git 저장소 검증과 변경 정보 수집
- `generator.py`: safe mode, 프롬프트, schema, 출력 검증
- `ai_client.py`: GroqCloud 요청과 응답 및 오류 처리
- `cli.py`: 옵션 파싱과 전체 실행 흐름

## 오류와 해결 방법

| 메시지 또는 상황 | 원인 | 해결 방법 |
| --- | --- | --- |
| `현재 위치는 Git 저장소가 아닙니다` | Git 저장소 밖에서 실행 | 저장소로 이동한 뒤 실행 |
| `프로젝트 루트에서 실행해 주세요` | 하위 디렉터리에서 실행 | 안내된 저장소 루트로 이동 |
| `AI_API_KEY 환경변수가 설정되지 않았습니다` | Key 미설정 | `.env`를 작성하고 현재 셸에 로드 |
| `Groq API 인증에 실패했습니다` | 잘못되거나 만료된 Key | GroqCloud에서 Key 확인 또는 재발급 |
| `Groq API 요청 한도를 초과했습니다` | HTTP 429 | 잠시 후 다시 실행 |
| `Groq API 네트워크 오류` | 연결 실패 또는 timeout | 네트워크 확인 후 재실행 |
| `Groq API 요청 실패 (HTTP ...)` | 그 밖의 API 요청 오류 | HTTP 상태와 응답 메시지 확인 |
| `Groq API 응답 JSON 형식이 올바르지 않습니다` | 응답 구조 또는 JSON 오류 | 모델과 옵션 확인 후 재실행 |
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
- Groq 전용 코드는 클라이언트 모듈에 격리
- 자동 실행보다 사람이 검토할 수 있는 초안 생성을 우선

## 제한 범위

- 커밋, push, PR 생성이나 merge를 자동으로 수행하지 않습니다.
- 저장소 루트에서만 실행할 수 있습니다.
- untracked 파일은 이름만 status에 포함되며 파일 내용은 diff에 포함되지 않습니다.
- binary diff와 Git이 제공하지 않는 파일 내용은 분석하지 못합니다.
- 생성 품질은 모델, diff 범위, 컨벤션 설정에 영향을 받습니다.
- safe mode는 일반적인 민감정보 패턴을 줄이기 위한 방어선이며 모든 형태를 보장하지 않습니다.
