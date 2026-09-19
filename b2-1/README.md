# Budget App

<p align="center">
  <b>표준 라이브러리만으로 만든 콘솔 가계부</b><br/>
  거래 기록부터 예산 관리, 반복 내역, 백업과 복구까지 지원하는 Python CLI 애플리케이션
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/dependencies-none-7CF0BD?style=flat-square" alt="No dependencies" />
  <img src="https://img.shields.io/badge/storage-JSONL-F7DF1E?style=flat-square" alt="JSONL storage" />
  <img src="https://img.shields.io/badge/interface-CLI-222222?style=flat-square" alt="CLI" />
</p>

---

## Overview

Budget App은 수입과 지출을 기록하고 월별 소비와 예산을 관리하는 콘솔 가계부입니다.

외부 패키지나 데이터베이스 없이 Python 표준 라이브러리와 JSONL 파일만 사용합니다. 단순히 데이터를 저장하는 것보다 **파일이 손상되거나 작업이 중단돼도 기존 데이터를 잃지 않는 구조**를 만드는 데 집중했습니다.

## Problem

파일 기반 프로그램은 구현이 간단하지만 데이터가 늘어날수록 다음 문제가 생길 수 있습니다.

- 저장 중 오류가 발생하면 기존 파일이 손상될 수 있음
- 읽을 수 없는 행을 건너뛰면 일부 데이터만 처리된 사실을 알기 어려움
- 여러 기능에서 서로 다른 기준으로 데이터를 검증하면 결과가 달라짐
- 반복 내역을 여러 번 적용하면 같은 거래가 중복될 수 있음
- 카테고리 변경처럼 여러 데이터가 연결된 작업에서 참조가 깨질 수 있음

## Solution

- 모든 조회와 재작성 경로가 같은 검증 정책을 사용
- 임시 파일에 먼저 쓴 뒤 `os.replace`로 교체
- 손상된 행을 삭제하지 않고 격리 디렉터리로 이동
- 반복 내역의 출처를 기록해 같은 달에는 한 번만 생성
- CLI, 서비스, 저장소, 모델의 의존 방향을 테스트로 검증
- 예상 가능한 오류를 종료 코드와 사용자 안내로 구분

## Core Features

- 수입과 지출 추가, 조회, 검색, 수정, 삭제
- 기간, 카테고리, 타입, 메모, 태그 검색
- 카테고리 추가, 삭제, 대체
- 월별 수입, 지출, 잔액 요약
- 월 예산 설정과 초과 경고
- CSV 가져오기와 내보내기
- 데이터 백업과 손상 행 복구
- 월 단위 반복 거래 생성
- 실행 시간과 오류 로그 기록
- 대화형 입력 검증과 재입력

## Commands

| 명령 | 설명 |
| --- | --- |
| `add` | 수입 또는 지출을 대화형으로 추가 |
| `list` | 최근 거래 목록 출력 |
| `search` | 기간, 타입, 카테고리, 메모, 태그 검색 |
| `update` | 거래의 금액, 메모, 태그 등 수정 |
| `delete` | 거래 삭제 |
| `category list` | 카테고리 목록 출력 |
| `category add` | 카테고리 추가 |
| `category remove` | 카테고리 삭제 또는 다른 카테고리로 대체 |
| `budget set` | 월별 예산 설정 |
| `budget list` | 설정된 예산 목록 출력 |
| `summary` | 월별 수입, 지출, 잔액과 예산 요약 |
| `import` | CSV 거래 가져오기 |
| `export` | 거래를 CSV로 내보내기 |
| `backup` | 현재 데이터 백업 |
| `repair` | 손상된 행을 격리하고 정상 데이터 복구 |
| `recurring add` | 반복 거래 규칙 추가 |
| `recurring list` | 반복 거래 규칙 조회 |
| `recurring apply` | 지정한 달의 반복 거래 생성 |
| `recurring remove` | 반복 거래 규칙 삭제 |

## Usage

### 거래 추가

```bash
python3 -m budget_app add
```

```text
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
카테고리: food
금액(양수): 15000
메모(선택): 점심
태그(쉼표로 구분, 없으면 엔터): meal
[저장 완료] id=TX-000012
```

### 목록과 검색

```bash
python3 -m budget_app list --limit 10

python3 -m budget_app search \
  --from 2024-01-01 \
  --to 2024-01-31 \
  --category food

python3 -m budget_app search \
  --type expense \
  --q 점심 \
  --tag meal
```

### 거래 수정과 삭제

```bash
python3 -m budget_app update \
  --id TX-000012 \
  --amount 20000 \
  --memo "점심 회식"

python3 -m budget_app delete --id TX-000012
```

### 월별 예산과 요약

```bash
python3 -m budget_app budget set \
  --month 2024-01 \
  --amount 500000

python3 -m budget_app summary \
  --month 2024-01 \
  --top 3
```

```text
총 수입: 3,000,000원
총 지출: 215,000원
잔액: 2,785,000원
예산: 500,000원 (사용률 43.0%)

지출 TOP 3
1) rent 150,000원
2) food 45,000원
3) transport 20,000원
```

### CSV 가져오기와 내보내기

```bash
python3 -m budget_app export \
  --out export.csv \
  --month 2024-01

python3 -m budget_app import \
  --from import.csv
```

정상 행만 반영하며, 실패한 행은 `<입력파일>.errors.csv`에 줄 번호와 실패 이유를 기록합니다.

### 백업과 복구

```bash
python3 -m budget_app backup
python3 -m budget_app repair
```

`repair`는 읽을 수 없는 행을 삭제하지 않고 `data/quarantine/`으로 옮깁니다. 사용자가 원문을 확인하고 직접 복구할 수 있습니다.

### 반복 거래

```bash
python3 -m budget_app recurring add
python3 -m budget_app recurring list
python3 -m budget_app recurring apply --month 2024-03
python3 -m budget_app recurring remove --id RR-3f9a2c17
```

같은 규칙을 같은 달에 여러 번 적용해도 거래는 한 번만 생성됩니다.

## Data

데이터는 한 줄에 하나의 JSON 객체를 저장하는 JSONL 형식으로 관리합니다.

```json
{"id":"TX-000012","type":"expense","date":"2024-01-15","amount":15000,"category":"food","memo":"점심","tags":["meal"]}
```

| 파일 | 내용 |
| --- | --- |
| `data/transactions.jsonl` | 수입과 지출 거래 |
| `data/categories.jsonl` | 카테고리 |
| `data/budgets.jsonl` | 월별 예산 |
| `data/recurring.jsonl` | 반복 거래 규칙 |
| `data/app.log` | 실행과 오류 로그 |
| `data/backups/` | 명령으로 생성한 데이터 백업 |
| `data/quarantine/` | 복구 과정에서 격리한 손상 행 |

JSONL을 사용해 파일 전체를 메모리에 올리지 않고 행 단위로 처리할 수 있습니다. 메모와 태그처럼 구조가 있는 데이터도 별도 인용 규칙 없이 저장할 수 있습니다.

## Architecture

```text
budget_app/
├── __main__.py       애플리케이션 진입점
├── errors.py         오류 계층과 종료 코드
├── validators.py     날짜, 금액, 타입, 카테고리 검증
├── models.py         데이터 구조와 불변식
├── storage.py        JSONL 읽기, 쓰기, 원자적 교체
├── decorators.py     오류 처리, 실행 로그, 시간 측정
├── service/
│   ├── ledger.py     거래 조회와 변경
│   ├── categories.py 카테고리 관리
│   ├── reports.py    예산과 월별 요약
│   ├── porting.py    CSV와 복구
│   ├── recurring.py  반복 거래
│   └── reading.py    공통 읽기 정책
└── cli/
    ├── parser.py     명령과 옵션 정의
    ├── app.py        명령 실행과 계층 조립
    ├── prompts.py    대화형 입력
    └── render.py     결과 출력
```

의존 방향은 다음과 같이 한쪽으로만 흐릅니다.

```text
CLI → Service → Storage → Models → Validators → Errors
```

`tests/test_architecture.py`가 모듈의 import 관계를 검사해 계층 규칙이 깨지지 않도록 합니다.

## Data Flow

```text
[사용자 명령]
      │
      ▼
CLI 파싱과 입력 검증
      │
      ▼
Service 업무 규칙
      │
      ▼
공통 읽기와 데이터 검증
      │
      ▼
Storage JSONL 처리
      │
      ├── 조회: 검증된 데이터 반환
      │
      └── 수정: 임시 파일 작성 → 원본 교체
      ▼
CLI 결과 또는 오류 안내
```

## Technical Highlights

| Area | Decision | Impact |
| --- | --- | --- |
| File Safety | 임시 파일 작성 후 `os.replace`로 교체 | 저장 도중 실패해도 기존 파일 유지 |
| Read Policy | 모든 기능이 같은 공통 읽기 경로 사용 | 조회와 수정의 검증 기준 일치 |
| Recovery | 손상 행을 삭제하지 않고 격리 | 원문 확인과 수동 복구 가능 |
| Recurring | 거래에 규칙 ID와 적용 월을 출처로 저장 | 반복 실행 시 중복 거래 방지 |
| Validation | 입력과 저장 데이터가 같은 검증 함수 사용 | CLI를 거치지 않은 잘못된 데이터도 감지 |
| Error Handling | 예상 오류를 종료 코드로 분류 | 자동화 환경에서 실패 원인 구분 가능 |
| Architecture Test | import 관계를 테스트로 검사 | 계층 간 의존 역전 방지 |
| Dependencies | Python 표준 라이브러리만 사용 | 별도의 패키지 설치 없이 실행 |

## Exit Codes

| 코드 | 의미 |
| --- | --- |
| `0` | 정상 종료 |
| `1` | 예상하지 못한 내부 오류 |
| `2` | 입력 또는 사용법 오류 |
| `3` | 거래, 카테고리, 반복 규칙을 찾을 수 없음 |
| `4` | 파일 입출력 오류 또는 데이터 손상 |

## Running Locally

```bash
git clone https://github.com/b0e2/codyssey.git
cd codyssey/b2-1

python3 -m budget_app --help
python3 -m budget_app add
```

외부 패키지가 없으므로 별도의 설치 과정은 필요하지 않습니다.

## Testing

```bash
python3 -m unittest discover -s tests
```

현재 모델, 저장소, 서비스, CLI, 데이터 안전성, 계층 규칙을 포함한 226개의 테스트가 있습니다.

## Known Limitations

- 마지막 거래를 삭제하면 표시용 거래 번호가 다시 사용될 수 있습니다.
- 파일 하나의 교체는 원자적이지만 여러 파일을 동시에 바꾸는 작업 전체는 원자적이지 않습니다.
- 여러 프로세스가 같은 데이터 디렉터리에 동시에 쓰는 상황은 지원하지 않습니다.
- 같은 CSV 파일을 여러 번 가져오면 거래가 중복될 수 있습니다.
- CSV에는 내부 거래 ID와 반복 거래 출처가 포함되지 않습니다.

## Roadmap

- 거래 ID 생성 방식 개선
- 여러 파일을 변경하는 작업의 트랜잭션 처리
- CSV 중복 가져오기 방지
- 동시 실행을 위한 파일 잠금
- 테스트 자동 실행을 위한 GitHub Actions 구성
