"""npu: MAC 연산 기반 Mini NPU 시뮬레이터 패키지.

입력 패턴과 두 필터(Cross, X)의 MAC 점수를 비교해 어느 쪽에 가까운지 판별한다.

- core:     상수/정책, 라벨 정규화, 행렬 자료구조, MAC 연산·판정
- patterns: N x N Cross / X 패턴 생성
- bench:    MAC 연산의 성능 측정과 결과 표
- dataset:  data.json 로드 및 스키마 검증/판정
- cli:      콘솔 입출력 헬퍼 및 실행 흐름(run_*)
"""
