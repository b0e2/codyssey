"""Mini NPU Simulator.

AI가 이미지를 인식하는 핵심 원리인 MAC(Multiply-Accumulate) 연산을
순수 파이썬 표준 라이브러리만으로 흉내 내는 콘솔 애플리케이션.

두 개의 필터(Cross, X) 중 입력 패턴과 더 유사한(점수가 높은) 쪽을 골라
"이 패턴은 십자가인가, X인가"를 판별한다.

외부 라이브러리(NumPy, pandas 등) 사용 금지 — json, time 등 표준 라이브러리만 사용.
"""

import json
import os
import time

# ---------------------------------------------------------------------------
# 상수 / 정책
# ---------------------------------------------------------------------------

# 점수 비교 허용오차(epsilon). 부동소수점 오차로 인한 미세한 차이는 동점으로 본다.
EPSILON = 1e-9

# 프로그램 내부에서 사용하는 표준 라벨.
LABEL_CROSS = "Cross"
LABEL_X = "X"
LABEL_UNDECIDED = "UNDECIDED"

# data.json 위치 (실행 위치와 무관하게 항상 같은 파일을 찾도록 절대 경로로 계산).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "data.json")


# ---------------------------------------------------------------------------
# 라벨 정규화(표준화)
# ---------------------------------------------------------------------------

def normalize_label(raw):
    """다양한 표기의 라벨을 표준 라벨(Cross / X)로 정규화한다.

    - 'cross', '+', 'Cross'  -> 'Cross'
    - 'x', 'X'               -> 'X'

    정규화 규칙에 없는 값이면 ValueError 를 발생시켜 상위에서 케이스 단위로
    처리(FAIL)할 수 있게 한다.
    """
    if raw is None:
        raise ValueError("라벨이 비어 있습니다.")

    key = str(raw).strip().lower()
    if key in ("cross", "+"):
        return LABEL_CROSS
    if key in ("x",):
        return LABEL_X
    raise ValueError("알 수 없는 라벨: {!r}".format(raw))


# ---------------------------------------------------------------------------
# 2차원 행렬(패턴/필터) 데이터 구조
# ---------------------------------------------------------------------------
# 행렬은 파이썬 기본 자료구조인 list-of-list(2차원 리스트)로 표현한다.
# 요구사항("특정 위치의 값을 저장/읽기")을 명시적으로 드러내기 위해
# 전용 접근 함수(create_matrix / get_cell / set_cell)를 제공한다.

def create_matrix(n, fill=0.0):
    """n x n 크기의 2차원 행렬을 생성한다(모든 칸을 fill 값으로 초기화)."""
    return [[fill for _ in range(n)] for _ in range(n)]


def get_cell(matrix, row, col):
    """행렬의 (row, col) 위치 값을 읽어온다."""
    return matrix[row][col]


def set_cell(matrix, row, col, value):
    """행렬의 (row, col) 위치에 값을 저장한다."""
    matrix[row][col] = value


def matrix_size(matrix):
    """정사각 행렬의 한 변 길이(N)를 반환한다. 정사각형이 아니면 ValueError."""
    rows = len(matrix)
    for r in matrix:
        if len(r) != rows:
            raise ValueError(
                "정사각 행렬이 아닙니다: {}행 x {}열".format(rows, len(r))
            )
    return rows


# ---------------------------------------------------------------------------
# MAC(Multiply-Accumulate) 연산
# ---------------------------------------------------------------------------

def mac_2d(pattern, filt):
    """패턴과 필터를 같은 위치끼리 곱하고 모두 더한 점수를 반환한다.

    NumPy 등 벡터화 라이브러리 없이 이중 반복문으로 직접 구현한다.
    두 행렬의 크기가 다르면 ValueError 를 발생시킨다.
    """
    n = matrix_size(pattern)
    m = matrix_size(filt)
    if n != m:
        raise ValueError(
            "크기 불일치: 패턴 {n}x{n} vs 필터 {m}x{m}".format(n=n, m=m)
        )

    score = 0.0
    for i in range(n):
        for j in range(n):
            score += pattern[i][j] * filt[i][j]
    return score


# ---------------------------------------------------------------------------
# 판정 / 시간 측정 유틸
# ---------------------------------------------------------------------------

def judge(score_cross, score_x, epsilon=EPSILON):
    """두 점수를 epsilon 기반으로 비교하여 표준 라벨을 반환한다.

    |Cross - X| < epsilon 이면 동점으로 보고 UNDECIDED 를 반환한다.
    """
    if abs(score_cross - score_x) < epsilon:
        return LABEL_UNDECIDED
    return LABEL_CROSS if score_cross > score_x else LABEL_X


def measure_mac_ms(pattern, filt, repeat=10):
    """MAC 연산을 repeat 회 반복 측정하여 1회 평균 시간을 ms 단위로 반환한다.

    I/O(입력/출력/파일 읽기)를 제외하고 순수 연산 구간만 측정한다.
    """
    if repeat < 1:
        repeat = 1
    start = time.perf_counter()
    for _ in range(repeat):
        mac_2d(pattern, filt)
    elapsed = time.perf_counter() - start
    return (elapsed / repeat) * 1000.0


# ---------------------------------------------------------------------------
# 모드 (이후 커밋에서 구현)
# ---------------------------------------------------------------------------

def run_mode1():
    """모드 1: 사용자 입력(3x3). 후속 커밋에서 구현."""
    print("[모드 1] 아직 구현되지 않았습니다.")


def run_mode2():
    """모드 2: data.json 분석. 후속 커밋에서 구현."""
    print("[모드 2] 아직 구현되지 않았습니다.")


# ---------------------------------------------------------------------------
# 진입점 / 메뉴
# ---------------------------------------------------------------------------

def main():
    print("=== Mini NPU Simulator ===")
    print()
    print("[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")

    choice = input("선택: ").strip()
    print()

    if choice == "1":
        run_mode1()
    elif choice == "2":
        run_mode2()
    else:
        print("잘못된 선택입니다. 1 또는 2를 입력하세요.")


if __name__ == "__main__":
    main()
