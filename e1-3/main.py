"""Mini NPU Simulator - 진입점.

AI가 이미지를 인식하는 핵심 원리인 MAC(Multiply-Accumulate) 연산을
순수 파이썬 표준 라이브러리만으로 흉내 내는 콘솔 애플리케이션.

두 개의 필터(Cross, X) 중 입력 패턴과 더 유사한(점수가 높은) 쪽을 골라
"이 패턴은 십자가인가, X인가"를 판별한다.

실제 로직은 npu 패키지에 계층별로 분리되어 있다:
    npu.core    - 상수/정책, 라벨 정규화, 행렬 자료구조, MAC 연산·판정
    npu.dataset - data.json 로드 및 스키마 검증/판정
    npu.bench   - 성능 측정 및 패턴 생성
    npu.cli     - 콘솔 입력 헬퍼 및 실행 흐름(run_*)
"""

from npu.cli import (
    OperationCancelled,
    read_line,
    run_mode1,
    run_mode2,
    run_optimization_compare,
    run_pattern_generator,
)

# 메뉴 번호 -> (설명, 실행 함수)
MENU = {
    "1": ("사용자 입력 (3x3)", run_mode1),
    "2": ("data.json 분석", run_mode2),
    "3": ("최적화 비교 2D vs 1D (보너스)", run_optimization_compare),
    "4": ("패턴 생성기 (보너스)", run_pattern_generator),
}

EXIT_CHOICES = ("0", "q", "quit", "exit", "종료")


def print_menu():
    print("[모드 선택]")
    for key in sorted(MENU):
        print("{0}. {1}".format(key, MENU[key][0]))
    print("0. 종료")


def main():
    """메뉴를 반복 출력해 여러 모드를 연속으로 실행한다.

    작업 중 Ctrl+C 는 해당 작업만 취소하고 메뉴로 돌아오며,
    예기치 못한 오류가 나도 메시지를 출력한 뒤 메뉴를 유지한다.
    """
    print("=== Mini NPU Simulator ===")
    print("(작업 중 Ctrl+C: 취소 후 메뉴로 / 메뉴에서 0 또는 Ctrl+C: 종료)")

    while True:
        print()
        print_menu()
        choice = read_line("선택: ", cancellable=False).strip().lower()
        print()

        if choice in EXIT_CHOICES:
            print("프로그램을 종료합니다.")
            return

        entry = MENU.get(choice)
        if entry is None:
            print("잘못된 선택입니다. 0 ~ {0} 중에서 선택하세요.".format(max(MENU)))
            continue

        try:
            entry[1]()
        except OperationCancelled:
            continue
        except Exception as exc:  # 어떤 오류에도 프로그램이 죽지 않게 한다.
            print("실행 중 오류가 발생했습니다: {0}: {1}".format(
                type(exc).__name__, exc))

        print()
        print("-" * 42)


if __name__ == "__main__":
    main()
