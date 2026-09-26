"""N x N Cross / X 패턴 생성기.

임의의 크기 N에 대해 판별 대상이 되는 두 기준 패턴을 만든다.
생성 결과는 모드 1의 필터와 성능 분석의 표본으로 재사용된다.

core 외에는 의존하지 않으며, 출력(print)은 담당하지 않는다.
"""

from .core import create_matrix, set_cell


def generate_cross(n):
    """N x N 십자가(Cross) 패턴을 생성한다.

    가운데 행과 가운데 열에 해당하는 칸만 1.0 이고 나머지는 0.0 이다.
    """
    mid = n // 2
    matrix = create_matrix(n)
    for i in range(n):
        for j in range(n):
            if i == mid or j == mid:
                set_cell(matrix, i, j, 1.0)
    return matrix


def generate_x(n):
    """N x N X 패턴을 생성한다.

    두 대각선(i == j, i + j == n - 1)에 해당하는 칸만 1.0 이고 나머지는 0.0 이다.
    """
    matrix = create_matrix(n)
    for i in range(n):
        for j in range(n):
            if i == j or i + j == n - 1:
                set_cell(matrix, i, j, 1.0)
    return matrix
