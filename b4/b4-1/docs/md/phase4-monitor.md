# Phase 4. monitor.sh

기록: [log/phase4-monitor.log](../log/phase4-monitor.log) · 소스: [scripts/monitor.sh](../../scripts/monitor.sh)

## 목표

| 항목 | 요구 |
| --- | --- |
| 위치 | `$AGENT_HOME/bin/monitor.sh`, agent-dev:agent-core, 750 |
| 헬스 체크 | 앱 프로세스, 15034 LISTEN. 비정상이면 exit 1 |
| 방화벽 | 비활성이면 `[WARNING]`만 출력 |
| 자원 | CPU, 메모리, 루트 디스크 사용률 |
| 임계값 | CPU > 20%, MEM > 10%, DISK > 80% 이면 `[WARNING]` |
| 로그 | `/var/log/agent-app/monitor.log`, `[YYYY-MM-DD HH:MM:SS] PID:... CPU:..% MEM:..% DISK_USED:..%` |
| 용량 | 10MB, 10개 파일 |

## 구현

| 항목 | 방법 |
| --- | --- |
| 프로세스 | `pgrep -n -x agent-app-linux` |
| 포트 | `ss -tlnH "sport = :15034"` |
| 방화벽 | `/etc/ufw/ufw.conf`의 `ENABLED=yes` |
| CPU | `/proc/stat`을 1초 간격으로 두 번 읽어 차이로 계산 |
| 메모리 | `free`의 (total - available) / total |
| 디스크 | `df -P /`의 Use% |
| 소수 비교 | awk |
| 용량 관리 | 10MB 이상이면 `monitor.<시각>.log`로 옮기고 보관본 9개 + 현재 1개 유지 |

작업하면서 정한 것들:

- 프로세스 검색: 리눅스는 프로세스 이름을 15자까지만 저장해서 `agent-app-linux-arm64`가 `agent-app-linux`로 보인다. `pgrep -f`는 명령줄 전체를 검색해서 확인하는 셸 자신까지 잡혔기 때문에 이름 정확히 일치(`-x`)로 찾는다. 부모/자식 2개 중 포트를 연 자식을 가리키도록 `-n`(가장 나중에 뜬 것)을 붙였다.
- 방화벽 확인: `ufw status`는 root만 실행할 수 있다. cron으로 도는 agent-admin은 쓸 수 없어서, 누구나 읽을 수 있는 설정 파일 값을 확인한다. `ufw enable`/`disable`을 하면 이 값이 바뀐다.
- CPU 계산: `/proc/stat`은 부팅 후 누적값이라 한 번만 읽으면 평균이 된다. 1초 간격으로 두 번 읽어 그 사이 사용률을 구했다.
- 메모리 계산: 리눅스는 남는 메모리를 캐시로 쓰기 때문에 free 대신 available을 기준으로 했다.
- 환경 변수 기본값: cron에는 profile.d 변수가 없어서 `${AGENT_HOME:-/home/agent-admin/agent-app}` 형태로 기본값을 뒀다.
- 실패 기록: 헬스 체크 실패 시 원인을 monitor.log에도 남긴다. cron 실행 중에는 화면 출력을 볼 수 없어서, 이게 없으면 언제 왜 멈췄는지 알 수 없다.
- 보관 파일 이름: `.log`로 끝나게 해서 로그 보존 정책(7일 경과 `*.log` 압축) 대상에 들어가게 했다.

## 배치

```bash
sudo mkdir -p /home/agent-admin/agent-app/bin
sudo chown agent-dev:agent-core /home/agent-admin/agent-app/bin
sudo chmod 750 /home/agent-admin/agent-app/bin
sudo cp /Users/jeongbin/Desktop/b4-1/scripts/monitor.sh /home/agent-admin/agent-app/bin/
sudo chown agent-dev:agent-core /home/agent-admin/agent-app/bin/monitor.sh
sudo chmod 750 /home/agent-admin/agent-app/bin/monitor.sh
```

```
-rwxr-x--- 1 agent-dev agent-core 3435 Sep 28 07:29 monitor.sh
```

agent-dev가 작성자(수정 가능), agent-admin은 agent-core 그룹 권한으로 실행만 가능하다. agent-test는 읽을 수도 없다.

## 확인

```
agent-admin@agent-lab:~$ $AGENT_HOME/bin/monitor.sh
====== SYSTEM MONITOR RESULT ======

[HEALTH CHECK]
Checking process 'agent-app-linux'... [OK] (PID: 5755)
Checking port 15034... [OK]
Checking firewall (ufw)... [OK]

[RESOURCE MONITORING]
CPU Usage : 37.7%
MEM Usage : 15.1%
DISK Used : 8%

[WARNING] CPU threshold exceeded (37.7% > 20%)
[WARNING] MEM threshold exceeded (15.1% > 10%)

[INFO] Log appended: /var/log/agent-app/monitor.log
```

| 상황 | 방법 | 결과 | 종료 코드 |
| --- | --- | --- | --- |
| 정상 | agent-admin 실행 | 로그 1줄 추가 | 0 |
| CPU 경고 | `yes` 3개로 부하 | `CPU threshold exceeded` | 0 |
| 방화벽 비활성 | `sudo ufw disable` | `[WARNING] Firewall (ufw) is not active` | 0 |
| 앱 중단 | `sudo pkill -INT -x agent-app-linux` | `[ERROR] process 'agent-app-linux' not running` | 1 |
| 권한 없는 계정 | agent-test 실행 | Permission denied | 126 |
| 로그 회전 | 임시 폴더, `LOG_MAX_BYTES=1`로 22회 | 파일 10개 유지 | 0 |

머신 코어가 7개라 앱이 코어 하나를 다 써도 전체의 약 14%다. 앱만으로는 CPU 경고가 나오지 않아서 `yes` 3개로 부하를 줘서 확인했다.

```
$ sudo tail -8 /var/log/agent-app/monitor.log
[2026-09-28 07:31:10] PID:5755 CPU:2.4% MEM:15.3% DISK_USED:8%
[2026-09-28 07:31:12] PID:5755 CPU:0.2% MEM:14.7% DISK_USED:8%
[2026-09-28 07:31:13] PID:5755 CPU:0.2% MEM:14.1% DISK_USED:8%
[2026-09-28 07:31:14] PID:5755 CPU:1.7% MEM:14.7% DISK_USED:8%
[2026-09-28 07:31:18] PID:5755 CPU:37.7% MEM:15.1% DISK_USED:8%
[2026-09-28 07:31:26] PID:5755 CPU:2.4% MEM:16.7% DISK_USED:8%
[2026-09-28 07:31:31] ERROR: process 'agent-app-linux' not running
[2026-09-28 07:31:37] PID:6934 CPU:1.7% MEM:15.5% DISK_USED:8%
```

앱 중단 시점의 원인과 재실행 후 바뀐 PID가 함께 남는다.
