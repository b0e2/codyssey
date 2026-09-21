# AI GitGen

Git 변경 사항을 기반으로 커밋 메시지와 Pull Request 초안을 생성하는 Python CLI 도구입니다.

## 요구 환경

- Python 3.10 이상
- Git
- GroqCloud API Key

## 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 환경변수

```bash
cp .env.example .env
```

`.env` 파일에 발급받은 Key를 입력한 뒤 현재 터미널에 불러옵니다.

```bash
set -a
source .env
set +a
```

API Key는 코드에 작성하거나 Git에 포함하지 않습니다.

## 명령어

```bash
ai-gitgen commit
ai-gitgen pr
```

모듈 방식으로도 실행할 수 있습니다.

```bash
python -m ai_gitgen commit
python -m ai_gitgen pr
```

주요 옵션:

```bash
ai-gitgen commit \
  --model openai/gpt-oss-20b \
  --temperature 0.2 \
  --max-tokens 800
```

- 기본 모델: `openai/gpt-oss-20b`
- 품질 우선 모델: `openai/gpt-oss-120b`
- commit 기본 최대 토큰: `800`
- PR 기본 최대 토큰: `1500`
- safe mode: 기본 활성화

현재 단계에서는 프로젝트 구조와 CLI 기본 옵션을 제공합니다. Git 변경 사항 수집과 GroqCloud API 호출은 다음 단계에서 구현합니다.
