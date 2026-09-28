# b4-1

Ubuntu 서버에 SSH, 방화벽, 계정 권한을 설정하고 agent-app을 실행한 뒤, 앱 상태와 자원 사용률을 cron으로 매분 기록하도록 구성했다.

## 환경

| 항목 | 값 |
| --- | --- |
| OS | Ubuntu 22.04.5 LTS (aarch64) |
| 실행 환경 | OrbStack Linux machine (macOS, Apple Silicon) |
| 앱 | `agent-app-linux-arm64` |
| 스크립트 | Bash |

## 구성

### 보안

- SSH 포트 20022, root 원격 로그인 차단
- UFW 활성화, 인바운드 20022/tcp, 15034/tcp만 허용

### 계정과 권한

| 계정 | 역할 | 그룹 |
| --- | --- | --- |
| agent-admin | 운영, 앱 실행, cron 실행 | agent-common, agent-core |
| agent-dev | 개발, 스크립트 작성 | agent-common, agent-core |
| agent-test | QA | agent-common |

| 경로 | 소유자:그룹 | 권한 |
| --- | --- | --- |
| `/home/agent-admin/agent-app` | agent-admin:agent-common | 750 |
| `upload_files` | agent-admin:agent-common | 2770, default ACL |
| `api_keys` | agent-admin:agent-core | 2770, default ACL |
| `bin` | agent-dev:agent-core | 750 |
| `/var/log/agent-app` | agent-admin:agent-core | 2770, default ACL |
| `/var/log/monitor/agent-app/archive` | agent-admin:agent-core | 2770 |

`/home/agent-admin`에는 agent-common 통과 권한(ACL `--x`)을 추가했다.

### 환경 변수

`/etc/profile.d/agent-app.sh`

```bash
export AGENT_HOME=/home/agent-admin/agent-app
export AGENT_PORT=15034
export AGENT_UPLOAD_DIR=$AGENT_HOME/upload_files
export AGENT_KEY_PATH=$AGENT_HOME/api_keys
export AGENT_LOG_DIR=/var/log/agent-app
```

## 스크립트

| 파일 | 역할 | 실행 |
| --- | --- | --- |
| [monitor.sh](scripts/monitor.sh) | 프로세스, 포트, 방화벽 확인. CPU, 메모리, 디스크 사용률 기록 | cron 매분 |
| [report.sh](scripts/report.sh) | monitor.log 평균/최대/최소, 샘플 수 | 수동 |
| [log-archive.sh](scripts/log-archive.sh) | 7일 지난 로그 압축, 30일 지난 압축본 삭제 | cron 매일 03:00 |

서버에는 `$AGENT_HOME/bin/`에 agent-dev:agent-core 750으로 배치한다.

```bash
sudo -iu agent-admin

$AGENT_HOME/bin/monitor.sh
$AGENT_HOME/bin/report.sh
$AGENT_HOME/bin/report.sh "2026-09-28 07:30:00" "2026-09-28 08:00:00"
$AGENT_HOME/bin/log-archive.sh
```

monitor.log 형식:

```
[2026-09-28 07:37:02] PID:6934 CPU:2.5% MEM:17.3% DISK_USED:8%
```

crontab (agent-admin):

```
* * * * * /home/agent-admin/agent-app/bin/monitor.sh > /dev/null 2>&1
0 3 * * * /home/agent-admin/agent-app/bin/log-archive.sh >> /var/log/agent-app/log-archive.log 2>&1
```

## 앱 실행

```bash
sudo -iu agent-admin
nohup $AGENT_HOME/agent-app-linux-arm64 > /dev/null 2>&1 &
```

앱 로그는 `/var/log/agent-app/agent_app.log`에 기록된다.

## 확인 항목

| 항목 | 문서 | 기록 |
| --- | --- | --- |
| SSH 포트 변경, root 원격 접속 차단 | [Phase 1](docs/md/phase1-ssh-firewall.md) | [log](docs/log/phase1-ssh-firewall.log) |
| 방화벽 활성화, 20022/tcp, 15034/tcp 허용 | [Phase 1](docs/md/phase1-ssh-firewall.md) | [log](docs/log/phase1-ssh-firewall.log) |
| 계정, 그룹 생성 | [Phase 2](docs/md/phase2-account-permission.md) | [log](docs/log/phase2-account-permission.log) |
| 디렉토리 구조, 권한, ACL | [Phase 2](docs/md/phase2-account-permission.md) | [log](docs/log/phase2-account-permission.log) |
| Boot Sequence 5단계 [OK], Agent READY | [Phase 3](docs/md/phase3-app-env.md) | [log](docs/log/phase3-app-env.log) |
| monitor.sh 실행 결과 | [Phase 4](docs/md/phase4-monitor.md) | [log](docs/log/phase4-monitor.log) |
| monitor.log 누적 기록 | [Phase 4](docs/md/phase4-monitor.md), [Phase 5](docs/md/phase5-cron.md) | [log](docs/log/phase5-cron.log) |
| crontab 매분 실행, 로그 증가 | [Phase 5](docs/md/phase5-cron.md) | [log](docs/log/phase5-cron.log) |
| report.sh | [Phase 6-1](docs/md/phase6-report.md) | [log](docs/log/phase6-report.log) |
| 로그 압축, 보관, 삭제 | [Phase 6-2](docs/md/phase6-log-archive.md) | [log](docs/log/phase6-log-archive.log) |

`docs/md/`는 단계별 진행 문서, `docs/log/`는 터미널 작업 기록이다.

## 진행 문서

- [Phase 0. 실습 환경](docs/md/phase0-setup.md)
- [Phase 1. SSH, 방화벽](docs/md/phase1-ssh-firewall.md)
- [Phase 2. 계정, 그룹, 디렉토리 권한](docs/md/phase2-account-permission.md)
- [Phase 3. 앱 실행 환경](docs/md/phase3-app-env.md)
- [Phase 4. monitor.sh](docs/md/phase4-monitor.md)
- [Phase 5. cron 자동 실행](docs/md/phase5-cron.md)
- [Phase 6-1. report.sh](docs/md/phase6-report.md)
- [Phase 6-2. 로그 보존 정책](docs/md/phase6-log-archive.md)

## 키 경로

앱은 `AGENT_KEY_PATH`를 디렉토리로 받고, 그 안의 `secret.key`를 읽는다.

| 항목 | 값 |
| --- | --- |
| `AGENT_KEY_PATH` | `$AGENT_HOME/api_keys` |
| 키 파일 | `t_secret.key` |
| `secret.key` | `t_secret.key`를 가리키는 심볼릭 링크 |

자세한 내용은 [Phase 3](docs/md/phase3-app-env.md) 참고.

## 디렉토리 구조

```
b4-1/
├── README.md
├── docs/
│   ├── md/               단계별 진행 문서
│   └── log/              단계별 터미널 기록
└── scripts/
    ├── monitor.sh        앱 프로세스, 포트, 방화벽 확인 후 자원 사용률을 monitor.log에 기록
    ├── report.sh         monitor.log의 평균/최대/최소, 샘플 수 출력
    └── log-archive.sh    7일 지난 로그 압축 후 보관, 30일 지난 압축본 삭제
```
