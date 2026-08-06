"""콘솔 입출력 헬퍼와 각 모드의 실행 흐름(run_*).

core / patterns / bench / dataset 를 조립해 실제 화면 흐름을 만든다.
"""

import json

from .core import (
    EPSILON,
    create_matrix,
    set_cell,
    mac_2d,
    judge,
)
from .bench import (
    measure_mac_ms,
    performance_analysis,
    compare_optimization,
)
from .patterns import generate_cross, generate_x
from .dataset import (
    resolve_data_path,
    load_data,
    normalize_filters,
    analyze_pattern,
    pattern_sort_key,
)


# ---------------------------------------------------------------------------
# 콘솔 출력 헬퍼
# ---------------------------------------------------------------------------

def print_matrix(matrix):
    """행렬을 한 줄에 한 행씩 출력한다(값이 정수면 소수점을 생략)."""
    for row in matrix:
        cells = []
        for value in row:
            cells.append(
                str(int(value)) if float(value).is_integer() else str(value)
            )
        print(" ".join(cells))


# ---------------------------------------------------------------------------
# 콘솔 입력 헬퍼
# ---------------------------------------------------------------------------

class OperationCancelled(Exception):
    """작업 중 Ctrl+C 로 취소했음을 알린다. 메뉴 루프가 받아 메뉴로 복귀한다."""


def read_line(prompt="", cancellable=True):
    """한 줄을 입력받는다.

    - EOF(Ctrl+D, 파이프 종료): 안내 후 프로그램을 정상 종료한다.
    - Ctrl+C: cancellable 이면 OperationCancelled 로 현재 작업만 취소하고,
      아니면(메뉴 단계) 프로그램을 정상 종료한다.
    """
    try:
        return input(prompt)
    except EOFError:
        print()
        print("입력이 종료되었습니다. 프로그램을 종료합니다.")
        raise SystemExit(0)
    except KeyboardInterrupt:
        print()
        if cancellable:
            print("작업을 취소했습니다. 메뉴로 돌아갑니다.")
            raise OperationCancelled
        print("프로그램을 종료합니다.")
        raise SystemExit(0)


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
        line = read_line()
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
    """필터 A/B와 패턴을 3x3로 입력받아 MAC 점수·판정·연산 시간을 출력한다.

    필터는 직접 입력하거나, 패턴 생성기가 만든 3x3 Cross/X 를 재사용할 수 있다.
    """
    print("#----------------------------------------")
    print("# [1] 필터 입력")
    print("#----------------------------------------")
    print("1. 직접 입력")
    print("2. 패턴 생성기로 자동 생성 (A=Cross, B=X)")
    source = read_line("선택: ").strip()
    print()

    if source == "2":
        filter_a = generate_cross(3)
        filter_b = generate_x(3)
        print("필터 A (Cross) 자동 생성")
        print_matrix(filter_a)
        print()
        print("필터 B (X) 자동 생성")
        print_matrix(filter_b)
        print()
    else:
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


# ---------------------------------------------------------------------------
# 모드 2: data.json 분석
# ---------------------------------------------------------------------------

def run_mode2():
    """data.json 을 로드해 필터/패턴을 일괄 판정하고 결과를 리포트한다."""
    data_path = resolve_data_path()
    try:
        data = load_data(data_path)
    except FileNotFoundError:
        print("data.json 을 찾을 수 없습니다: {0}".format(data_path))
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
    for pattern_id in sorted(patterns, key=pattern_sort_key):
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


# ---------------------------------------------------------------------------
# 보너스 실행 흐름
# ---------------------------------------------------------------------------

def run_optimization_compare():
    """보너스: 2D vs 1D MAC 최적화 전/후 성능을 동일 조건으로 비교한다."""
    print("#----------------------------------------")
    print("# 최적화 비교: 2D 행렬 vs 1D 배열 (평균/10회)")
    print("#----------------------------------------")
    compare_optimization([3, 5, 13, 25])


def run_pattern_generator():
    """보너스: 크기 N 을 입력받아 Cross/X 패턴을 생성하고, 생성 패턴으로
    3x3 판정 예시와 성능 분석을 재활용해 보여준다."""
    while True:
        raw = read_line("생성할 패턴 크기 N 입력(예: 5): ").strip()
        try:
            n = int(raw)
            if n < 1:
                raise ValueError
            break
        except ValueError:
            print("입력 형식 오류: 1 이상의 정수를 입력하세요.")

    cross = generate_cross(n)
    x = generate_x(n)

    print()
    print("[생성된 Cross 패턴]")
    print_matrix(cross)
    print()
    print("[생성된 X 패턴]")
    print_matrix(x)
    print()

    # 생성 패턴을 필터로 재활용: Cross 패턴을 입력했을 때 올바로 판정되는지 확인.
    score_cross = mac_2d(cross, cross)
    score_x = mac_2d(cross, x)
    verdict = judge(score_cross, score_x)
    print("[검증] 입력=Cross 패턴 -> Cross 점수: {0}, X 점수: {1}, 판정: {2}".format(
        score_cross, score_x, verdict))
    print()

    print("[생성 패턴 성능 분석]")
    performance_analysis([n])
