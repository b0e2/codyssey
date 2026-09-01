"""핵심 도메인: 상수/정책, 라벨 정규화, 행렬 자료구조, MAC 연산·판정.

이 모듈은 다른 npu 모듈에 의존하지 않는 가장 하위 계층이다.
외부 라이브러리(NumPy 등) 없이 표준 라이브러리만 사용한다.
"""

# ---------------------------------------------------------------------------
# 상수 / 정책
# ---------------------------------------------------------------------------

# 점수 비교 허용오차(epsilon). 부동소수점 오차로 인한 미세한 차이는 동점으로 본다.
EPSILON = 1e-9

# 프로그램 내부에서 사용하는 표준 라벨.
LABEL_CROSS = "Cross"
LABEL_X = "X"
LABEL_UNDECIDED = "UNDECIDED"


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


def flatten(matrix):
    """n x n 2차원 행렬을 길이 N^2 의 1차원 리스트로 펼친다(행 우선)."""
    flat = []
    for row in matrix:
        flat.extend(row)
    return flat


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


def mac_1d(flat_pattern, flat_filter):
    """1차원으로 펼친 패턴/필터의 MAC 점수를 반환한다.

    같은 길이의 두 1차원 배열을 위치별로 곱해 누적한다(단일 반복문).
    """
    if len(flat_pattern) != len(flat_filter):
        raise ValueError("길이 불일치: {0} vs {1}".format(
            len(flat_pattern), len(flat_filter)))
    score = 0.0
    for i in range(len(flat_pattern)):
        score += flat_pattern[i] * flat_filter[i]
    return score


# ---------------------------------------------------------------------------
# 판정
# ---------------------------------------------------------------------------

def judge(score_cross, score_x, epsilon=EPSILON):
    """두 점수를 epsilon 기반으로 비교하여 표준 라벨을 반환한다.

    |Cross - X| < epsilon 이면 동점으로 보고 UNDECIDED 를 반환한다.
    """
    if abs(score_cross - score_x) < epsilon:
        return LABEL_UNDECIDED
    return LABEL_CROSS if score_cross > score_x else LABEL_X
