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
    read_line,
    run_mode1,
    run_mode2,
    run_optimization_compare,
    run_pattern_generator,
)


def main():
    print("=== Mini NPU Simulator ===")
    print()
    print("[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")
    print("3. 최적화 비교 2D vs 1D (보너스)")
    print("4. 패턴 생성기 (보너스)")

    choice = read_line("선택: ").strip()
    print()

    if choice == "1":
        run_mode1()
    elif choice == "2":
        run_mode2()
    elif choice == "3":
        run_optimization_compare()
    elif choice == "4":
        run_pattern_generator()
    else:
        print("잘못된 선택입니다. 1 ~ 4 중에서 선택하세요.")


if __name__ == "__main__":
    main()
