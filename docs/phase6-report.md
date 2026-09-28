# Phase 6-1. report.sh

기록: [sessions/phase6-report.log](sessions/phase6-report.log) · 소스: [scripts/report.sh](../scripts/report.sh)

## 목표

- monitor.log의 CPU, 메모리, 디스크 평균/최대/최소와 샘플 수 출력
- 시작/종료 시간을 받으면 해당 구간만 분석

## 구현

```bash
report.sh                                              # 전체
report.sh "2026-09-28 07:00:00" "2026-09-28 08:00:00"  # 구간
```

- 로그 한 줄을 공백으로 나누면 4~6번째 칸이 `CPU:2.4%`, `MEM:15.3%`, `DISK_USED:8%`다. awk로 칸을 나누고 `:`와 `%`를 떼어 숫자만 모았다.
- 4번째 칸이 `CPU:`로 시작하지 않는 줄(헬스 체크 실패 기록)은 제외한다.
- 시각은 `YYYY-MM-DD HH:MM:SS` 형식이라 문자열 비교와 시간 순서가 같다. 날짜 변환 없이 구간을 걸러냈다.
- Ubuntu 기본 awk가 mawk라서 gawk 전용 문법은 쓰지 않았다.
- 배치는 monitor.sh와 같게 agent-dev:agent-core 750.

## 확인

```
agent-admin@agent-lab:~$ wc -l < $AGENT_LOG_DIR/monitor.log
13
agent-admin@agent-lab:~$ $AGENT_HOME/bin/report.sh
====== STATISTICS REPORT ======
  Period : 2026-09-28 07:31:10 ~ 2026-09-28 07:39:02
  [CPU]
    Average : 4.5%
    Maximum : 37.7% at 2026-09-28 07:31:18
    Minimum : 0.1% at 2026-09-28 07:39:02
  [Memory]
    Average : 16.1%
    Maximum : 19.5% at 2026-09-28 07:36:02
    Minimum : 14.1% at 2026-09-28 07:31:13
  [Disk]
    Average : 8.0%
    Maximum : 8.0% at 2026-09-28 07:31:10
    Minimum : 8.0% at 2026-09-28 07:31:10
  [Samples]
    Data Points: 12 samples
```

13줄 중 실패 기록 1줄을 뺀 12개가 샘플로 잡혔다. 원본 로그를 awk로 따로 계산한 CPU 평균(4.5%, 12개)과 같았다.

```
agent-admin@agent-lab:~$ $AGENT_HOME/bin/report.sh "$(date -d '5 minutes ago' '+%F %T')" "$(date '+%F %T')"
====== STATISTICS REPORT ======
  Period : 2026-09-28 07:35:03 ~ 2026-09-28 07:39:02
  ...
  [Samples]
    Data Points: 5 samples
```

| 입력 | 출력 | 종료 코드 |
| --- | --- | --- |
| 인자 1개 | `Usage: ...` | 1 |
| 시간 형식 오류 | `[ERROR] Time format must be YYYY-MM-DD HH:MM:SS` | 1 |
| 시작 > 종료 | `[ERROR] Start time is later than end time` | 1 |
| 구간에 데이터 없음 | `[INFO] No samples in the given period` | 1 |
| 로그 파일 읽기 불가 | `[ERROR] Cannot read ...` | 1 |
