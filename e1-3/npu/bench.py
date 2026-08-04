"""성능 측정 및 패턴 생성.

- 시간 측정: measure_mac_ms / measure_mac_1d_ms
- 성능 표: performance_analysis / compare_optimization (보너스 1: 2D vs 1D)
- 패턴 생성기(보너스 2): generate_cross / generate_x / print_matrix
"""

import time

from .core import create_matrix, set_cell, flatten, mac_2d, mac_1d


# ---------------------------------------------------------------------------
# 시간 측정
# ---------------------------------------------------------------------------

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


def measure_mac_1d_ms(flat_pattern, flat_filter, repeat=10):
    """1차원 MAC 을 repeat 회 반복 측정하여 1회 평균 시간을 ms 로 반환한다."""
    if repeat < 1:
        repeat = 1
    start = time.perf_counter()
    for _ in range(repeat):
        mac_1d(flat_pattern, flat_filter)
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


def compare_optimization(sizes, repeat=10):
    """동일 입력·동일 반복으로 2D MAC 과 1D MAC 의 시간을 비교 출력한다(보너스)."""
    print("크기       2D(ms)      1D(ms)      속도향상")
    print("---------------------------------------------")
    for n in sizes:
        pattern = _sample_matrix(n)
        filt = _sample_matrix(n)
        flat_p = flatten(pattern)
        flat_f = flatten(filt)
        t2d = measure_mac_ms(pattern, filt, repeat=repeat)
        t1d = measure_mac_1d_ms(flat_p, flat_f, repeat=repeat)
        speedup = (t2d / t1d) if t1d > 0 else float("inf")
        label = "{0}x{0}".format(n)
        print("{0:<10} {1:>8.4f}   {2:>8.4f}   {3:>7.2f}x".format(
            label, t2d, t1d, speedup))


# ---------------------------------------------------------------------------
# 패턴 생성기 - N x N Cross / X 자동 생성 (보너스 2)
# ---------------------------------------------------------------------------

def generate_cross(n):
    """N x N 십자가(Cross) 패턴을 생성한다(가운데 행/열이 1)."""
    mid = n // 2
    matrix = create_matrix(n)
    for i in range(n):
        for j in range(n):
            if i == mid or j == mid:
                set_cell(matrix, i, j, 1.0)
    return matrix


def generate_x(n):
    """N x N X 패턴을 생성한다(두 대각선이 1)."""
    matrix = create_matrix(n)
    for i in range(n):
        for j in range(n):
            if i == j or i + j == n - 1:
                set_cell(matrix, i, j, 1.0)
    return matrix


def print_matrix(matrix):
    """행렬을 사람이 보기 좋게(정수는 정수로) 콘솔에 출력한다."""
    for row in matrix:
        cells = []
        for v in row:
            cells.append(str(int(v)) if float(v).is_integer() else str(v))
        print(" ".join(cells))
