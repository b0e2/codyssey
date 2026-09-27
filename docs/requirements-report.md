# 요구사항 수행 내역서

## 1. 실습 환경

| 항목 | 값 |
| --- | --- |
| 호스트 | macOS (Apple Silicon), OrbStack |
| 실습 머신 | OrbStack Linux machine `agent-lab` |
| OS | Ubuntu 22.04.5 LTS, aarch64 |
| 앱 | `agent-app-linux-arm64` |
| 작업 기록 | `docs/sessions/*.log` (터미널 세션 기록) |

| 기록 파일 | 내용 |
| --- | --- |
| [phase0-install.log](sessions/phase0-install.log) | 머신 생성, 패키지 설치 |
| [phase1-ssh-firewall.log](sessions/phase1-ssh-firewall.log) | SSH, 방화벽 |
| [phase2-account-permission.log](sessions/phase2-account-permission.log) | 계정, 그룹, 디렉토리, ACL |
| [phase3-app-env.log](sessions/phase3-app-env.log) | 환경 변수, 키 파일, 앱 실행 |
| [phase4-monitor.log](sessions/phase4-monitor.log) | monitor.sh 배치, 실행 |
| [phase5-cron.log](sessions/phase5-cron.log) | cron 등록, 자동 실행 |
| [phase6-report.log](sessions/phase6-report.log) | report.sh |
| [phase6-log-archive.log](sessions/phase6-log-archive.log) | log-archive.sh |

## 2. 수행 내역

### 2.1 SSH

```bash
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak
sudo sed -i 's/^#\?Port .*/Port 20022/' /etc/ssh/sshd_config
sudo sed -i 's/^#\?PermitRootLogin .*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sshd -t
sudo systemctl restart ssh
```

### 2.2 방화벽 (UFW)

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 20022/tcp
sudo ufw allow 15034/tcp
sudo ufw enable
```

### 2.3 계정, 그룹

```bash
sudo groupadd agent-common
sudo groupadd agent-core
sudo useradd -m -s /bin/bash -G agent-common,agent-core agent-admin
sudo useradd -m -s /bin/bash -G agent-common,agent-core agent-dev
sudo useradd -m -s /bin/bash -G agent-common agent-test
```

### 2.4 디렉토리, 권한, ACL

```bash
sudo mkdir -p /home/agent-admin/agent-app/upload_files
sudo mkdir -p /home/agent-admin/agent-app/api_keys
sudo mkdir -p /var/log/agent-app

sudo chown agent-admin:agent-common /home/agent-admin/agent-app
sudo chmod 750 /home/agent-admin/agent-app
sudo chown agent-admin:agent-common /home/agent-admin/agent-app/upload_files
sudo chmod 2770 /home/agent-admin/agent-app/upload_files
sudo chown agent-admin:agent-core /home/agent-admin/agent-app/api_keys
sudo chmod 2770 /home/agent-admin/agent-app/api_keys
sudo chown agent-admin:agent-core /var/log/agent-app
sudo chmod 2770 /var/log/agent-app

sudo setfacl -m g:agent-common:x /home/agent-admin
sudo setfacl -d -m g:agent-common:rwx /home/agent-admin/agent-app/upload_files
sudo setfacl -d -m g:agent-core:rwx /home/agent-admin/agent-app/api_keys
sudo setfacl -d -m g:agent-core:rwx /var/log/agent-app
```

| 경로 | 소유자:그룹 | 권한 | 접근 |
| --- | --- | --- | --- |
| `/home/agent-admin` | agent-admin:agent-admin | `750` + ACL `g:agent-common:--x` | agent-common 통과만 |
| `$AGENT_HOME` | agent-admin:agent-common | `750` | agent-common 진입 |
| `upload_files` | agent-admin:agent-common | `2770` + default ACL | agent-common 읽기/쓰기 |
| `api_keys` | agent-admin:agent-core | `2770` + default ACL | agent-core만 읽기/쓰기 |
| `/var/log/agent-app` | agent-admin:agent-core | `2770` + default ACL | agent-core만 읽기/쓰기 |
| `$AGENT_HOME/bin` | agent-dev:agent-core | `750` | agent-core 실행 |

- setgid(`2`): 디렉토리 안에 생성되는 파일이 디렉토리 그룹을 상속
- default ACL: 생성되는 파일에 그룹 읽기/쓰기 권한 상속
- `/home/agent-admin` ACL: Ubuntu 22.04 홈 기본 권한 `750`(`HOME_MODE 0750`)에서 agent-dev, agent-test가 `upload_files`에 도달하기 위한 통과 권한

### 2.5 환경 변수, 키 파일, 앱

```bash
sudo apt-get install -y unzip
unzip -o /Users/jeongbin/Downloads/agent-app.zip agent-app-linux-arm64 -d /tmp
sudo cp /tmp/agent-app-linux-arm64 /home/agent-admin/agent-app/
sudo chown agent-admin:agent-core /home/agent-admin/agent-app/agent-app-linux-arm64
sudo chmod 750 /home/agent-admin/agent-app/agent-app-linux-arm64

echo 'agent_api_key_test' | sudo tee /home/agent-admin/agent-app/api_keys/t_secret.key
sudo chown agent-admin:agent-core /home/agent-admin/agent-app/api_keys/t_secret.key
sudo ln -s t_secret.key /home/agent-admin/agent-app/api_keys/secret.key
sudo chown -h agent-admin:agent-core /home/agent-admin/agent-app/api_keys/secret.key

sudo tee /etc/profile.d/agent-app.sh <<'EOF'
export AGENT_HOME=/home/agent-admin/agent-app
export AGENT_PORT=15034
export AGENT_UPLOAD_DIR=$AGENT_HOME/upload_files
export AGENT_KEY_PATH=$AGENT_HOME/api_keys
export AGENT_LOG_DIR=/var/log/agent-app
EOF
```

```bash
sudo -iu agent-admin
nohup $AGENT_HOME/agent-app-linux-arm64 > /dev/null 2>&1 &
```

`AGENT_KEY_PATH`와 키 파일 이름은 [5. 명세와 제공 앱의 차이](#5-명세와-제공-앱의-차이) 참고.

### 2.6 monitor.sh

```bash
sudo mkdir -p /home/agent-admin/agent-app/bin
sudo chown agent-dev:agent-core /home/agent-admin/agent-app/bin
sudo chmod 750 /home/agent-admin/agent-app/bin
sudo cp scripts/monitor.sh /home/agent-admin/agent-app/bin/
sudo chown agent-dev:agent-core /home/agent-admin/agent-app/bin/monitor.sh
sudo chmod 750 /home/agent-admin/agent-app/bin/monitor.sh
```

소스: [scripts/monitor.sh](../scripts/monitor.sh)

| 항목 | 구현 |
| --- | --- |
| 프로세스 | `pgrep -n -x agent-app-linux`, 없으면 로그 기록 후 exit 1 |
| 포트 | `ss -tlnH "sport = :15034"`, 없으면 로그 기록 후 exit 1 |
| 방화벽 | `/etc/ufw/ufw.conf`의 `ENABLED=yes`, 아니면 `[WARNING]` |
| CPU | `/proc/stat` 1초 간격 두 번 읽어 사용률 계산 |
| 메모리 | `free`의 (total - available) / total |
| 디스크 | `df -P /`의 Use% |
| 임계값 | CPU > 20, MEM > 10, DISK > 80 이면 `[WARNING]` |
| 로그 | `/var/log/agent-app/monitor.log` |
| 용량 관리 | 10MB 이상이면 `monitor.<시각>.log`로 보관, `monitor.log` 포함 10개 유지 |
| 환경 변수 | cron 실행을 위해 `AGENT_HOME`, `AGENT_PORT`, `AGENT_LOG_DIR` 기본값 지정 |

### 2.7 cron

```bash
sudo -iu agent-admin
echo '* * * * * /home/agent-admin/agent-app/bin/monitor.sh > /dev/null 2>&1' | crontab -
(crontab -l; echo '0 3 * * * /home/agent-admin/agent-app/bin/log-archive.sh >> /var/log/agent-app/log-archive.log 2>&1') | crontab -
```

## 3. 필수 증거 자료 체크리스트

| # | 항목 | 결과 | 기록 |
| --- | --- | --- | --- |
| 1 | SSH 포트 변경(20022), Root 원격 접속 차단 | 확인 | phase1-ssh-firewall.log |
| 2 | UFW 활성화, 20022/tcp, 15034/tcp만 허용 | 확인 | phase1-ssh-firewall.log |
| 3 | 계정/그룹 생성 | 확인 | phase2-account-permission.log |
| 4 | 디렉토리 구조, 권한(ACL 포함) | 확인 | phase2-account-permission.log |
| 5 | Boot Sequence 5단계 [OK], Agent READY | 확인 | phase3-app-env.log |
| 6 | monitor.sh 실행 결과 | 확인 | phase4-monitor.log |
| 7 | monitor.log 누적 기록 | 확인 | phase4-monitor.log, phase5-cron.log |
| 8 | crontab 매분 실행, 1분 후 로그 증가 | 확인 | phase5-cron.log |

### 3.1 SSH 포트 변경, Root 원격 접속 차단

```
$ grep -nE '^(Port|PermitRootLogin) ' /etc/ssh/sshd_config
14:Port 20022
33:PermitRootLogin no

$ sudo ss -tlnp | grep sshd
LISTEN 0      128          0.0.0.0:20022      0.0.0.0:*    users:(("sshd",pid=3292,fd=3))
LISTEN 0      128             [::]:20022         [::]:*    users:(("sshd",pid=3292,fd=4))
```

### 3.2 방화벽

```
$ sudo ufw status verbose
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
20022/tcp                  ALLOW IN    Anywhere
15034/tcp                  ALLOW IN    Anywhere
20022/tcp (v6)             ALLOW IN    Anywhere (v6)
15034/tcp (v6)             ALLOW IN    Anywhere (v6)
```

### 3.3 계정, 그룹

```
$ id agent-admin
uid=1000(agent-admin) gid=1002(agent-admin) groups=1002(agent-admin),1000(agent-common),1001(agent-core)
$ id agent-dev
uid=1001(agent-dev) gid=1003(agent-dev) groups=1003(agent-dev),1000(agent-common),1001(agent-core)
$ id agent-test
uid=1002(agent-test) gid=1004(agent-test) groups=1004(agent-test),1000(agent-common)

$ getent group agent-common agent-core
agent-common:x:1000:agent-admin,agent-dev,agent-test
agent-core:x:1001:agent-admin,agent-dev
```

### 3.4 디렉토리, 권한, ACL

```
$ sudo ls -ld /home/agent-admin /home/agent-admin/agent-app /home/agent-admin/agent-app/upload_files /home/agent-admin/agent-app/api_keys /var/log/agent-app
drwxr-x---+ 1 agent-admin agent-admin  72 Sep 28 07:09 /home/agent-admin
drwxr-x---  1 agent-admin agent-common 40 Sep 28 07:09 /home/agent-admin/agent-app
drwxrws---+ 1 agent-admin agent-core    0 Sep 28 07:09 /home/agent-admin/agent-app/api_keys
drwxrws---+ 1 agent-admin agent-common  0 Sep 28 07:09 /home/agent-admin/agent-app/upload_files
drwxrws---+ 1 agent-admin agent-core    0 Sep 28 07:09 /var/log/agent-app

$ sudo getfacl -p /home/agent-admin/agent-app/upload_files
# file: /home/agent-admin/agent-app/upload_files
# owner: agent-admin
# group: agent-common
# flags: -s-
user::rwx
group::rwx
other::---
default:user::rwx
default:group::rwx
default:group:agent-common:rwx
default:mask::rwx
default:other::---
```

계정별 접근 테스트:

| 테스트 | 결과 |
| --- | --- |
| agent-test → upload_files 파일 생성 | 성공 |
| agent-dev → agent-test가 생성한 파일 수정 | 성공 (`-rw-rw----+ agent-test agent-common`) |
| agent-test → api_keys 목록 | `Permission denied` |
| agent-test → /var/log/agent-app 쓰기 | `Permission denied` |
| agent-dev → /var/log/agent-app 쓰기 | 성공 |
| agent-test → /home/agent-admin 목록 | `Permission denied` |

### 3.5 Boot Sequence

```
agent-admin@agent-lab:~$ $AGENT_HOME/agent-app-linux-arm64
>>> Starting Agent Boot Sequence...
[1/5] Checking User Account               [OK]
   ... Running as service user 'agent-admin' (uid=1000)
[2/5] Verifying Environment Variables     [OK]
   ... All required Envs correct
[3/5] Checking Required Files             [OK]
   ... Verified 'secret.key' with correct key string.
[4/5] Checking Port Availability          [OK]
   ... Port 15034 is available.
[5/5] Verifying Log Permission            [OK]
   ... Log directory is writable: /var/log/agent-app
------------------------------------------------------------
All Boot Checks Passed!
Agent READY
```

```
$ ps -o user,pid,ppid,etime,cmd -u agent-admin
USER         PID    PPID     ELAPSED CMD
agent-a+    4271       1       00:05 /home/agent-admin/agent-app/agent-app-linux-arm64
agent-a+    4272    4271       00:04 /home/agent-admin/agent-app/agent-app-linux-arm64

$ sudo ss -tlnp | grep 15034
LISTEN 0      1            0.0.0.0:15034      0.0.0.0:*    users:(("agent-app-linux",pid=4272,fd=4))
```

### 3.6 monitor.sh 실행 결과

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

| 상황 | 결과 | 종료 코드 |
| --- | --- | --- |
| 정상 | 로그 1줄 추가 | 0 |
| 방화벽 비활성 (`ufw disable`) | `[WARNING] Firewall (ufw) is not active` | 0 |
| 앱 중단 (`pkill -INT`) | `[ERROR] process 'agent-app-linux' not running` | 1 |
| agent-test 실행 | `Permission denied` | 126 |

- 머신 코어가 7개라 앱의 단일 코어 부하는 전체의 약 14%다. CPU 경고는 `yes` 프로세스 3개로 부하를 주고 확인했다.
- 로그 용량 관리는 임시 디렉토리에서 `LOG_MAX_BYTES=1`로 22회 실행해 파일 10개 유지를 확인했다.

### 3.7 monitor.log 누적 기록

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

헬스 체크 실패 시 원인을 같은 로그에 기록한다. 앱 재기동 후 PID가 바뀐 것도 남는다.

### 3.8 crontab 자동 실행

```
agent-admin@agent-lab:~$ crontab -l
* * * * * /home/agent-admin/agent-app/bin/monitor.sh > /dev/null 2>&1

agent-admin@agent-lab:~$ date '+%F %T'; wc -l < $AGENT_LOG_DIR/monitor.log
2026-09-28 07:35:26
9
agent-admin@agent-lab:~$ sleep 125
agent-admin@agent-lab:~$ date '+%F %T'; wc -l < $AGENT_LOG_DIR/monitor.log
2026-09-28 07:37:32
11
agent-admin@agent-lab:~$ tail -4 $AGENT_LOG_DIR/monitor.log
[2026-09-28 07:31:37] PID:6934 CPU:1.7% MEM:15.5% DISK_USED:8%
[2026-09-28 07:35:03] PID:6934 CPU:1.1% MEM:14.5% DISK_USED:8%
[2026-09-28 07:36:02] PID:6934 CPU:2.1% MEM:19.5% DISK_USED:8%
[2026-09-28 07:37:02] PID:6934 CPU:2.5% MEM:17.3% DISK_USED:8%

$ sudo grep 'CRON.*agent-admin' /var/log/syslog | tail -3
Sep 28 07:36:01 agent-lab CRON[7525]: (agent-admin) CMD (/home/agent-admin/agent-app/bin/monitor.sh > /dev/null 2>&1)
Sep 28 07:37:01 agent-lab CRON[7544]: (agent-admin) CMD (/home/agent-admin/agent-app/bin/monitor.sh > /dev/null 2>&1)
```

## 4. 요약 리포트, 로그 보존 정책

### 4.1 report.sh

소스: [scripts/report.sh](../scripts/report.sh)

```
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

- 시작/종료 시간 인자로 구간 분석: `report.sh "2026-09-28 07:30:00" "2026-09-28 07:40:00"`
- `ERROR` 줄은 통계에서 제외
- 인자 개수, 시간 형식, 구간 순서, 데이터 없음, 파일 접근 오류 시 메시지 출력 후 exit 1

### 4.2 log-archive.sh

소스: [scripts/log-archive.sh](../scripts/log-archive.sh)

| 동작 | 대상 |
| --- | --- |
| gzip 압축 후 이동 | `/var/log/agent-app/*.log` 중 7일 이상 경과 → `/var/log/monitor/agent-app/archive/` |
| 삭제 | `archive/*.gz` 중 30일 이상 경과 |

```
[2026-09-28 07:44:00] [INFO] Start (logs: /var/log/agent-app, archive: /var/log/monitor/agent-app/archive)
[2026-09-28 07:44:00] [INFO] Archived: monitor.20260920-030001.log -> /var/log/monitor/agent-app/archive/monitor.20260920-030001.log.gz
[2026-09-28 07:44:00] [INFO] Deleted: monitor.20260825-030001.log.gz
[2026-09-28 07:44:00] [INFO] Done (archived: 1, skipped: 0, deleted: 1)
```

`touch -d`로 수정 시각을 8일 전, 3일 전, 31일 전, 20일 전으로 지정한 테스트 파일로 확인했다. 8일 전 로그와 31일 전 아카이브만 처리됐다.

| 상황 | 결과 | 종료 코드 |
| --- | --- | --- |
| 대상 0개 | `No logs older than 7 days`, `No archives older than 30 days` | 0 |
| 로그 디렉토리 없음 | `[WARNING] Log directory not found, skip compression` | 0 |
| 로그 디렉토리 쓰기 권한 없음 | `[WARNING] No write permission, skip compression` | 0 |
| 아카이브 디렉토리 생성 불가 | `[ERROR] Cannot create archive directory` | 1 |
| 같은 이름 압축본 존재 | `[WARNING] Already archived, skip` | 0 |

매일 03:00 cron 실행, 결과는 `/var/log/agent-app/log-archive.log`에 누적.

## 5. 명세와 제공 앱의 차이

명세 값으로 설정하면 Boot Sequence가 실패한다.

| 항목 | 명세 | 앱 요구 | 앱 메시지 |
| --- | --- | --- | --- |
| `AGENT_KEY_PATH` | `$AGENT_HOME/api_keys/t_secret.key` | `$AGENT_HOME/api_keys` | `Key Path Mismatch. Expected: /home/agent-admin/agent-app/api_keys` |
| 키 파일 이름 | `t_secret.key` | `secret.key` | `Missing File: secret.key` |

- `agent-app-linux-arm64`, `agent-app-linux-x86` 모두 같은 값을 요구한다 (x86은 amd64 머신에서 확인).
- 성공 기준인 Boot 5단계 통과에 맞춰 `AGENT_KEY_PATH`는 디렉토리 경로로 설정했다.
- 키 파일은 명세대로 `t_secret.key`를 생성하고, `secret.key`는 `t_secret.key`를 가리키는 심볼릭 링크로 두었다.

## 6. 구현 참고 사항

| 항목 | 내용 |
| --- | --- |
| 방화벽 확인 | `ufw status`는 root 전용이라 agent-admin 실행 시 `/etc/ufw/ufw.conf`의 `ENABLED` 값으로 확인 |
| 프로세스 이름 | 프로세스 이름(comm)은 15자로 잘려 `agent-app-linux`로 검색. 앱은 부모/자식 2개로 실행되어 `-n`으로 포트를 연 자식 PID 선택 |
| 헬스 체크 실패 기록 | cron 실행 시 화면 출력이 남지 않으므로 실패 원인을 monitor.log에 기록 |
| 보관 로그 이름 | `monitor.<시각>.log`로 `.log` 확장자를 유지해 7일 경과 압축 대상에 포함 |
| 앱 실행 | agent-admin 계정으로 `nohup` 백그라운드 실행. 앱이 `agent_app.log`를 직접 기록하므로 표준 출력은 사용하지 않음 |
