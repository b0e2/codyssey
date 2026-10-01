# Phase 2. monitor.sh

기록: [phase2-monitor.log](../log/phase2-monitor.log) · 코드: [scripts/monitor.sh](../../scripts/monitor.sh) · [#5](https://github.com/b0e2/b4-2/issues/5)

## 목표

- agent-leak-app 프로세스 단위 CPU, 메모리 기록
- 시스템 전체 사용률과 비교
- 로그가 멈춘 상태(무응답) 확인

## 기록 형식

```
[2026-10-01 01:20:18] PID:2421 STAT:S THREADS:3 CPU:1.3% RSS:116MB MEM:2.9% SYS_CPU:0.2% SYS_MEM:13.6% LOG_IDLE:0s
```

| 필드 | 출처 | 내용 |
| --- | --- | --- |
| `PID` | `pgrep -n -x agent-leak-app-` | 실제 동작하는 자식 프로세스 |
| `STAT`, `THREADS` | `/proc/PID/status` | 프로세스 상태, 스레드 수 |
| `CPU` | `/proc/PID/stat` utime + stime | 3초 동안 프로세스 CPU 사용률 (코어 1개 기준) |
| `RSS`, `MEM` | `/proc/PID/status` VmRSS | 물리 메모리 사용량, 전체 대비 비율 |
| `SYS_CPU`, `SYS_MEM` | `/proc/stat`, `free` | 시스템 전체 사용률 |
| `LOG_IDLE` | `stat -c %Y agent_app.log` | 앱 로그 마지막 기록 이후 경과 시간 |

- CPU 측정 구간을 3초로 둔 이유: 앱의 부하 작업이 약 3초 주기로 짧게 실행되어 1초 측정은 값이 0과 몇 %를 오갑니다.
- 프로세스가 없으면 `PROCESS:down`을 기록하고 1로 종료합니다. 반복 실행 중 앱이 종료되면 반복도 멈춥니다.

## 진행

```bash
sudo install -D -o agent-admin -g agent-admin -m 750 scripts/monitor.sh /home/agent-admin/agent-app/bin/monitor.sh
sudo -iu agent-admin
nohup $AGENT_HOME/agent-leak-app-arm64 > $AGENT_LOG_DIR/console.log 2>&1 &
pgrep -a -x agent-leak-app-
~/agent-app/bin/monitor.sh
kill %1
~/agent-app/bin/monitor.sh; echo "exit=$?"
cat $AGENT_LOG_DIR/monitor.log
```

## 확인

![monitor.sh](../images/monitor.png)

## 장애 재현 시 사용 방식

```bash
(sleep 2; while ~/agent-app/bin/monitor.sh > /dev/null; do :; done) &
$AGENT_HOME/agent-leak-app-arm64
```

앱을 앞에서 실행하고 관제는 백그라운드로 약 3초마다 `monitor.log`에 기록합니다. 앱의 종료 메시지는 화면에만 출력되어 앱을 앞에 둡니다.
