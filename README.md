# b4-2

agent-leak-app 실행 중 발생하는 메모리 누수, CPU 과점유, 교착상태 분석

## 장애 리포트

| 유형 | Issue | 원인 | 조치 | 결과 |
| --- | --- | --- | --- | --- |
| OOM | [#7](https://github.com/b0e2/b4-2/issues/7) | 힙 메모리 누적, MemoryGuard SIGKILL | `MEMORY_LIMIT` 256 → 512 | 33초 종료 → 2분 이상 동작 |
| CPU | [#9](https://github.com/b0e2/b4-2/issues/9) | 부하 50% 초과 시 Watchdog SIGTERM | `CPU_MAX_OCCUPY` 80 → 30 | 30초 종료 → 1분 36초 이상 동작 |
| Deadlock | [#11](https://github.com/b0e2/b4-2/issues/11) | 워커 스레드 2개의 락 순환 대기 | `MULTI_THREAD_ENABLE` true → false | 로그 정지 → 정상 진행 |
| 스케줄링 | [#13](https://github.com/b0e2/b4-2/issues/13) | 비선점형 Priority (B > C > A) | - | - |

## 실행 환경

- OrbStack Linux machine `leak-lab` (Ubuntu 22.04.5 LTS, aarch64)
- 실행 계정 `agent-admin`
- 앱 `/home/agent-admin/agent-app/agent-leak-app-arm64`
- 환경 변수 `~agent-admin/.bash_profile`

| 변수 | 값 |
| --- | --- |
| `AGENT_HOME` | `/home/agent-admin/agent-app` |
| `AGENT_PORT` | `15034` |
| `AGENT_UPLOAD_DIR` | `$AGENT_HOME/upload_files` |
| `AGENT_KEY_PATH` | `$AGENT_HOME/api_keys` |
| `AGENT_LOG_DIR` | `/var/log/agent-app` |
| `MEMORY_LIMIT` | `512` |
| `CPU_MAX_OCCUPY` | `30` |
| `MULTI_THREAD_ENABLE` | `false` |

## 설정값별 동작

| 설정 | 동작 | 종료 코드 |
| --- | --- | --- |
| `MEMORY_LIMIT` 256 이하 | 힙 증가 후 `SELF-TERMINATED (Memory Limit Exceeded)` | 137 (SIGKILL) |
| `CPU_MAX_OCCUPY` 50 초과 | 부하 50% 초과 시 `WATCHDOG: INITIATING EMERGENCY ABORT (SIGTERM)` | 143 (SIGTERM) |
| `MULTI_THREAD_ENABLE=true` | `WAITING ... (Status: BLOCKED)` 이후 무응답 | 종료 안 됨 |
| 512 / 30 / false | 정상 동작, 한도 도달 시 캐시 정리, 부하 상한에서 cooldown | - |

## monitor.sh

`scripts/monitor.sh`는 agent-leak-app 자식 프로세스와 시스템 전체 자원 사용률을 3초 동안 측정해 `$AGENT_LOG_DIR/monitor.log`에 한 줄로 기록합니다.

```
[2026-10-01 01:24:52] PID:2551 STAT:S THREADS:1 CPU:0.3% RSS:141MB MEM:3.6% SYS_CPU:0.0% SYS_MEM:13.9% LOG_IDLE:2s
```

| 필드 | 내용 |
| --- | --- |
| `STAT`, `THREADS` | 프로세스 상태, 스레드 수 |
| `CPU` | 프로세스 CPU 사용률 (코어 1개 기준) |
| `RSS`, `MEM` | 프로세스 물리 메모리 사용량, 전체 메모리 대비 비율 |
| `SYS_CPU`, `SYS_MEM` | 시스템 전체 사용률 |
| `LOG_IDLE` | `agent_app.log` 마지막 기록 이후 경과 시간 |

프로세스가 없으면 `PROCESS:down`을 기록하고 1로 종료합니다.

```bash
sudo install -D -o agent-admin -g agent-admin -m 750 scripts/monitor.sh /home/agent-admin/agent-app/bin/monitor.sh
sudo -iu agent-admin
(sleep 2; while ~/agent-app/bin/monitor.sh > /dev/null; do :; done) &
$AGENT_HOME/agent-leak-app-arm64
cat $AGENT_LOG_DIR/monitor.log
```

## 저장소 구조

```
b4-2/
├── README.md
├── scripts/
│   └── monitor.sh
└── docs/
    └── log/
        ├── phase0-setup.log         실습 머신 구성
        ├── phase1-app-env.log       실행 계정, 환경 변수, 부팅 확인
        ├── phase2-monitor.log       monitor.sh 배치, 실행
        ├── phase3-oom.log           MEMORY_LIMIT 128, 256, 512 실행
        ├── phase4-cpu.log           CPU_MAX_OCCUPY 80, 100, 30 실행
        ├── phase5-deadlock.log      MULTI_THREAD_ENABLE true, false 실행
        └── phase6-scheduling.log    스케줄러 작업 로그 수집
```

`docs/log/`는 터미널 입력과 출력을 그대로 기록한 파일입니다.
