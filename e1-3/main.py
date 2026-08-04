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
# 성능 분석
# ---------------------------------------------------------------------------

def _sample_matrix(n):
    """성능 측정용 n x n 표본 행렬. 0이 아닌 값이 섞이도록 결정적으로 채운다."""
    matrix = create_matrix(n)
    for i in range(n):
        for j in range(n):
            set_cell(matrix, i, j, float((i * n + j) % 3) + 0.5)
    return matrix


def performance_analysis(sizes, repeat=10):
    """크기별 MAC 연산의 평균 시간(ms)과 연산 횟수(N^2)를 표로 출력한다.

    각 크기마다 표본 패턴/필터를 만들어 repeat 회 반복 측정한다.
    I/O 시간을 제외하고 순수 연산 구간(measure_mac_ms)만 측정한다.
    """
    print("크기       평균 시간(ms)    연산 횟수(N^2)")
    print("---------------------------------------------")
    for n in sizes:
        pattern = _sample_matrix(n)
        filt = _sample_matrix(n)
        avg_ms = measure_mac_ms(pattern, filt, repeat=repeat)
        label = "{0}x{0}".format(n)
        print("{0:<10} {1:>12.4f}    {2:>10}".format(label, avg_ms, n * n))


# ---------------------------------------------------------------------------
# 콘솔 입력 헬퍼
# ---------------------------------------------------------------------------

def read_matrix(n, title):
    """콘솔에서 n x n 행렬을 한 줄씩(공백 구분) 입력받는다.

    각 줄은 정확히 n개의 숫자를 공백으로 구분해 입력해야 한다.
    행/열 개수 불일치 또는 숫자 파싱 실패 시 안내 문구를 출력하고
    해당 줄을 다시 입력받는다(재입력 유도).
    """
    print(title)
    matrix = create_matrix(n)
    row = 0
    while row < n:
        line = input()
        tokens = line.split()
        if len(tokens) != n:
            print(
                "입력 형식 오류: 각 줄에 {0}개의 숫자를 공백으로 구분해 "
                "입력하세요. (현재 {1}개)".format(n, len(tokens))
            )
            continue
        try:
            values = [float(tok) for tok in tokens]
        except ValueError:
            print("입력 형식 오류: 숫자만 입력하세요. (예: 0 1 0)")
            continue
        for col in range(n):
            set_cell(matrix, row, col, values[col])
        row += 1
    return matrix


# ---------------------------------------------------------------------------
# 모드 1: 사용자 입력(3x3)
# ---------------------------------------------------------------------------

def run_mode1():
    """필터 A/B와 패턴을 3x3로 입력받아 MAC 점수·판정·연산 시간을 출력한다."""
    print("#----------------------------------------")
    print("# [1] 필터 입력")
    print("#----------------------------------------")
    filter_a = read_matrix(3, "필터 A (3줄 입력, 공백 구분)")
    print("  -> 필터 A 저장 완료")
    print()
    filter_b = read_matrix(3, "필터 B (3줄 입력, 공백 구분)")
    print("  -> 필터 B 저장 완료")
    print()

    print("#----------------------------------------")
    print("# [2] 패턴 입력")
    print("#----------------------------------------")
    pattern = read_matrix(3, "패턴 (3줄 입력, 공백 구분)")
    print("  -> 패턴 저장 완료")
    print()

    score_a = mac_2d(pattern, filter_a)
    score_b = mac_2d(pattern, filter_b)
    avg_ms = (measure_mac_ms(pattern, filter_a) +
              measure_mac_ms(pattern, filter_b)) / 2.0

    # 필터 A/B 기준 판정(동점은 판정 불가).
    if abs(score_a - score_b) < EPSILON:
        verdict = "판정 불가 (|A-B| < {0})".format(EPSILON)
    else:
        verdict = "A" if score_a > score_b else "B"

    print("#----------------------------------------")
    print("# [3] MAC 결과")
    print("#----------------------------------------")
    print("A 점수: {0}".format(score_a))
    print("B 점수: {0}".format(score_b))
    print("연산 시간(평균/10회): {0:.3f} ms".format(avg_ms))
    print("판정: {0}".format(verdict))
    print()

    print("#----------------------------------------")
    print("# [4] 성능 분석 (평균/10회)")
    print("#----------------------------------------")
    performance_analysis([3])


def load_data(path):
    """data.json 을 읽어 파이썬 딕셔너리로 반환한다.

    파일이 없거나 JSON 파싱에 실패하면 예외를 그대로 올려 상위에서 안내한다.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_size_from_key(key):
    """'size_5_1' 형태의 패턴 키에서 크기 N(정수)을 추출한다."""
    parts = key.split("_")
    if len(parts) < 2 or parts[0] != "size":
        raise ValueError("패턴 키 형식 오류: {!r}".format(key))
    return int(parts[1])


def normalize_filters(raw_filters):
    """filters 원본을 {N: {'Cross': matrix, 'X': matrix}} 구조로 정규화한다.

    필터 키('cross'/'x')를 표준 라벨로 정규화한다. 반환값과 함께,
    로드된 크기(N) 목록을 정렬해 돌려준다.
    """
    normalized = {}
    for size_key, filt_pair in raw_filters.items():
        n = parse_size_from_key(size_key)
        std_pair = {}
        for label_key, matrix in filt_pair.items():
            std_pair[normalize_label(label_key)] = matrix
        normalized[n] = std_pair
    return normalized


def analyze_pattern(pattern_id, entry, filters):
    """패턴 1건을 분석해 결과 딕셔너리를 반환한다.

    스키마/크기 문제나 라벨 문제가 있어도 예외를 밖으로 던지지 않고
    status='FAIL' 과 reason 을 담아 반환한다(프로그램 비정상 종료 방지).
    """
    result = {
        "id": pattern_id,
        "cross": None,
        "x": None,
        "verdict": None,
        "expected": None,
        "status": "FAIL",
        "reason": "",
    }
    try:
        n = parse_size_from_key(pattern_id)
        pattern = entry["input"]
        expected = normalize_label(entry["expected"])
        result["expected"] = expected

        if n not in filters:
            result["reason"] = "size_{0} 필터가 없습니다".format(n)
            return result

        pair = filters[n]
        # 패턴이 정사각인지, 필터와 크기가 일치하는지 검증.
        p_size = matrix_size(pattern)
        if p_size != n:
            result["reason"] = (
                "크기 불일치: 키의 N={0} vs 패턴 {1}x{1}".format(n, p_size)
            )
            return result

        score_cross = mac_2d(pattern, pair[LABEL_CROSS])
        score_x = mac_2d(pattern, pair[LABEL_X])
        result["cross"] = score_cross
        result["x"] = score_x

        verdict = judge(score_cross, score_x)
        result["verdict"] = verdict

        if verdict == LABEL_UNDECIDED:
            result["reason"] = "동점(UNDECIDED) 규칙에 따라 FAIL"
        elif verdict == expected:
            result["status"] = "PASS"
        else:
            result["reason"] = "판정({0}) != expected({1})".format(
                verdict, expected
            )
    except (KeyError, ValueError, TypeError) as exc:
        result["reason"] = "스키마/데이터 오류: {0}".format(exc)
    return result


def run_mode2():
    """data.json 을 로드해 필터/패턴을 일괄 판정하고 결과를 리포트한다."""
    try:
        data = load_data(DATA_PATH)
    except FileNotFoundError:
        print("data.json 을 찾을 수 없습니다: {0}".format(DATA_PATH))
        return
    except json.JSONDecodeError as exc:
        print("data.json 파싱 실패: {0}".format(exc))
        return

    # [1] 필터 로드 (라벨 정규화)
    print("#----------------------------------------")
    print("# [1] 필터 로드")
    print("#----------------------------------------")
    try:
        filters = normalize_filters(data["filters"])
    except (KeyError, ValueError) as exc:
        print("필터 로드 실패: {0}".format(exc))
        return
    for n in sorted(filters):
        labels = ", ".join(sorted(filters[n]))
        print("✓ size_{0:<3} 필터 로드 완료 ({1})".format(n, labels))
    print()

    # [2] 패턴 분석
    print("#----------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#----------------------------------------")
    patterns = data.get("patterns", {})
    results = []
    for pattern_id in sorted(patterns, key=_pattern_sort_key):
        res = analyze_pattern(pattern_id, patterns[pattern_id], filters)
        results.append(res)

        print("--- {0} ---".format(pattern_id))
        if res["cross"] is not None:
            print("Cross 점수: {0}".format(res["cross"]))
            print("X 점수: {0}".format(res["x"]))
        expected = res["expected"] if res["expected"] is not None else "?"
        verdict = res["verdict"] if res["verdict"] is not None else "-"
        if res["status"] == "PASS":
            print("판정: {0} | expected: {1} | PASS".format(verdict, expected))
        else:
            print("판정: {0} | expected: {1} | FAIL ({2})".format(
                verdict, expected, res["reason"]))
    print()

    # [3] 성능 분석
    print("#----------------------------------------")
    print("# [3] 성능 분석 (평균/10회)")
    print("#----------------------------------------")
    performance_analysis([3, 5, 13, 25])
    print()

    # [4] 결과 요약
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = total - passed
    print("#----------------------------------------")
    print("# [4] 결과 요약")
    print("#----------------------------------------")
    print("총 테스트: {0}개".format(total))
    print("통과: {0}개".format(passed))
    print("실패: {0}개".format(failed))
    if failed:
        print()
        print("실패 케이스:")
        for r in results:
            if r["status"] == "FAIL":
                print("- {0}: {1}".format(r["id"], r["reason"]))


def _pattern_sort_key(key):
    """패턴 키를 (N, idx) 기준으로 자연 정렬하기 위한 보조 키."""
    parts = key.split("_")
    try:
        return (int(parts[1]), int(parts[2]))
    except (IndexError, ValueError):
        return (0, key)


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
