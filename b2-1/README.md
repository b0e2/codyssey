# budget_app

표준 라이브러리만 사용하는 콘솔 가계부. 수입·지출을 기록하고 월별로 요약하며, 예산 초과를 경고한다.

- Python 3.10 이상
- 외부 패키지 없음 (`pip install` 불필요)

## 실행

```bash
python -m budget_app <command> [options]
python -m budget_app --help          # 전체 명령
python -m budget_app search --help   # 명령별 옵션
```

전역 옵션은 서브커맨드 앞뒤 어디에 와도 된다.

| 옵션 | 설명 |
| --- | --- |
| `--data-dir <경로>` | 데이터 디렉터리 (기본 `./data`) |
| `--verbose` | 실행 시간 출력 |

## 저장 파일

처음 실행하면 데이터 디렉터리를 만들고 기본 카테고리(`food, transport, rent, salary, etc`)를 등록한다.

| 파일 | 내용 |
| --- | --- |
| `data/transactions.jsonl` | 거래 |
| `data/categories.jsonl` | 카테고리 |
| `data/budgets.jsonl` | 월 예산 |
| `data/recurring.jsonl` | 반복 규칙 |
| `data/app.log` | 실행 로그 (메모·태그는 길이만 기록) |
| `data/backups/<타임스탬프>/` | `backup` 으로 만든 사본 |

형식은 **JSONL** — 한 줄에 JSON 객체 하나다. 행이 곧 스트리밍 단위여서 파일 전체를 메모리에 올리지 않고 읽을 수 있고, 태그 배열이나 쉼표가 들어간 메모를 이스케이프 없이 담을 수 있다.

```json
{"id": "TX-000012", "type": "expense", "date": "2024-01-15", "amount": 15000, "category": "food", "memo": "점심", "tags": ["meal"]}
```

## 명령

### 거래 추가 — 대화형

```
$ python -m budget_app add
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
카테고리: food
금액(양수): 15000
메모(선택): 점심
태그(쉼표로 구분, 없으면 엔터): meal
[저장 완료] id=TX-000012
```

항목 하나가 틀리면 그 항목만 다시 묻는다. 3회 실패하면 중단한다.

### 목록·검색

```bash
python -m budget_app list --limit 10
python -m budget_app search --from 2024-01-01 --to 2024-01-31 --category food
python -m budget_app search --type expense --q 점심 --tag meal
```

출력은 최신순(`날짜 내림차순`, 같은 날이면 나중에 등록한 것 먼저)이다.
`--q` 는 메모를 부분 일치로 찾고 대소문자를 구분하지 않는다. `--tag` 는 태그 전체가 일치해야 하며 역시 대소문자를 구분하지 않는다. 카테고리는 대소문자를 구분한다. 기간은 양 끝을 포함한다.

### 수정·삭제

**`update` 는 옵션 방식이다.** `--id` 와 변경할 필드를 함께 준다.

```bash
python -m budget_app update --id TX-000012 --amount 20000 --memo "점심 회식"
python -m budget_app update --id TX-000012 --memo ""     # 메모 지우기
python -m budget_app delete --id TX-000012
```

옵션을 주지 않은 필드는 그대로 두고, 빈 문자열(`""`)을 주면 그 값을 지운다.

### 카테고리

```bash
python -m budget_app category list
python -m budget_app category add                          # 대화형
python -m budget_app category remove --name food --replace-with etc
```

사용 중인 카테고리는 `--replace-with` 없이는 지울 수 없다. 대체 카테고리를 주면 해당 거래를 모두 옮긴 뒤 삭제한다.

### 예산·요약

```bash
python -m budget_app budget set --month 2024-01 --amount 500000
python -m budget_app budget list
python -m budget_app summary --month 2024-01 --top 3
```

```
총 수입: 3,000,000원
총 지출: 215,000원
잔액: 2,785,000원
예산: 500,000원 (사용률 43.0%)

지출 TOP 3
1) rent 150,000원
2) food 45,000원
3) transport 20,000원
```

예산을 넘기면 `[경고] 예산을 N원 초과했습니다.` 가 함께 나온다. 정확히 100%는 초과가 아니다.
예산을 설정하지 않았거나 그 달에 거래가 없는 것은 오류가 아니며 종료 코드 0이다.

### 가져오기·내보내기

```bash
python -m budget_app export --out export.csv --month 2024-01
python -m budget_app export --out export.csv --from 2024-01-01 --to 2024-03-31
python -m budget_app import --from import.csv
```

`export` 는 `--month` 또는 `--from`/`--to` 중 **하나를 반드시** 받는다(둘을 같이 쓸 수는 없다).

### 백업·반복 내역

```bash
python -m budget_app backup
python -m budget_app recurring add                        # 대화형
python -m budget_app recurring list
python -m budget_app recurring apply --month 2024-03
python -m budget_app recurring remove --id RR-3f9a2c17
```

`apply` 는 같은 달에 여러 번 실행해도 거래를 한 번만 만든다. 생성한 거래에 `<규칙 id>:<월>` 을 출처로 남겨 두기 때문이다. 규칙의 일자가 그 달에 없으면(예: 31일 → 2월) 말일로 옮긴다.

## CSV 스키마

UTF-8, 헤더 포함. `import` 와 `export` 가 같은 형식을 쓴다.

| column | required | 설명 |
| --- | --- | --- |
| `date` | Y | `YYYY-MM-DD` |
| `type` | Y | `income` / `expense` |
| `category` | Y | 등록된 카테고리 |
| `amount` | Y | 양수 정수 |
| `memo` | N | 문자열 |
| `tags` | N | 쉼표로 구분한 문자열 |

```csv
date,type,category,amount,memo,tags
2024-01-15,expense,food,15000,"점심, 회식","meal,work"
```

`tags` 의 구분자와 CSV 필드 구분자가 모두 쉼표라, 값은 표준 방식대로 큰따옴표로 감싼다. 이 때문에 **태그 값 자체에는 쉼표를 넣을 수 없다.**

`import` 는 행 단위로 검증해 **정상 행만 반영**한다. 실패한 행은 `<입력파일>.errors.csv` 에 줄 번호와 이유를 남긴다.

```
$ python -m budget_app import --from import.csv
[완료] imported=2, skipped=3 (상세: import.csv.errors.csv)
```

## 종료 코드

| 코드 | 의미 |
| --- | --- |
| 0 | 정상 (결과가 비어 있는 경우 포함) |
| 1 | 예상치 못한 내부 오류 |
| 2 | 입력·사용법 오류 |
| 3 | 대상을 찾을 수 없음 (거래 id, 카테고리, 규칙) |
| 4 | 파일 입출력 오류 또는 데이터 손상 |

오류는 스택트레이스 대신 원인과 힌트로 보여준다. 스택트레이스는 `data/app.log` 에만 남는다.

```
$ python -m budget_app add
날짜(YYYY-MM-DD): 2024-13-40
[오류] 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).
[힌트] 예: 2024-01-15
```

## 구조

```
budget_app/
├── __main__.py     진입점
├── models.py       데이터 구조와 불변식 (아무것도 의존하지 않는다)
├── storage.py      JSONL 읽기·쓰기, 원자적 교체
├── decorators.py   오류 처리·실행 로그·시간 측정
├── service/        업무 규칙 (ledger / reports / porting / recurring)
└── cli/            명령행 파싱과 출력 (app / render)
```

의존은 한 방향으로만 흐른다: `cli → service → storage → models`.
`tests/test_architecture.py` 가 각 모듈의 import 를 검사해 이 방향을 강제한다. 폴더는 경계를 만들어 주지 않으므로 테스트로 확인한다.

## 알려진 한계

- **거래 번호가 재사용될 수 있다.** 다음 번호를 파일 마지막 행에서 얻기 때문에, 가장 마지막 거래를 지우면 그 번호가 다시 쓰인다. 번호는 표시용이고 다른 데이터가 참조하지 않아 문제가 되지 않는다. (반복 규칙 id 는 참조 대상이라 uuid 를 쓴다.)
- **원자성은 파일 하나 단위다.** 임시 파일에 쓰고 `os.replace` 로 바꾸므로 한 파일이 반쯤 쓰인 상태로 남지 않는다. 다만 `category remove --replace-with` 는 거래 파일과 카테고리 파일을 함께 바꾸며, 이 둘은 원자적이지 않다. 거래를 먼저 커밋하므로 중간에 실패해도 쓰이지 않는 카테고리가 남을 뿐 참조가 깨지지는 않는다.
- **동시 실행을 가정하지 않는다.** 여러 프로세스가 같은 데이터 디렉터리에 동시에 쓰면 결과를 보장하지 않는다.
- **CSV 에는 `id` 와 `source` 가 없다.** 같은 파일을 두 번 `import` 하면 거래가 중복되고, 반복 내역을 CSV 로 내보냈다 다시 가져오면 출처가 사라져 같은 달에 `apply` 할 때 다시 생성된다.
- **읽기 명령은 손상된 행을 건너뛴다.** 건너뛴 줄 번호를 `stderr` 로 알리되 종료 코드는 0이므로, 자동화에서는 `stderr` 를 함께 확인해야 한다. 파일을 통째로 다시 쓰는 명령(`update`/`delete`/`category remove`/`import`)은 손상 행이 있으면 원본을 건드리지 않고 중단한다.

## 테스트

```bash
python -m unittest discover -s tests
```
