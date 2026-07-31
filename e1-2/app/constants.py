"""여러 모듈이 공유하는 상수 정의."""

from pathlib import Path

# 프로젝트 루트의 state.json
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = PROJECT_ROOT / "state.json"
TEMP_STATE_PATH = PROJECT_ROOT / "state.json.tmp"

# 퀴즈 규칙
CHOICE_COUNT = 4
MIN_ANSWER = 1
MAX_ANSWER = CHOICE_COUNT

# 점수 규칙
PERFECT_SCORE = 100
HINT_PENALTY_RATIO = 0.5

# 기록 보관 / 표시 개수
HISTORY_LIMIT = 50
HISTORY_DISPLAY_COUNT = 5

# 카테고리
CATEGORY_PYTHON = "python"
CATEGORY_BACKEND = "backend"

CATEGORY_LABELS = {
    CATEGORY_PYTHON: "파이썬 문법",
    CATEGORY_BACKEND: "백엔드 기초",
}

CATEGORIES = tuple(CATEGORY_LABELS)

# 퀴즈 풀기에서 "전체"를 고를 때 쓰는 값 (실제 카테고리가 아니라 선택용)
CATEGORY_ALL = "all"