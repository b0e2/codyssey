# Phase 6-2. 로그 보존 정책

기록: [log/phase6-log-archive.log](../log/phase6-log-archive.log) · 소스: [scripts/log-archive.sh](../../scripts/log-archive.sh)

## 목표

| 동작 | 대상 |
| --- | --- |
| 압축 후 이동 | `/var/log/agent-app/*.log` 중 7일 이상 경과 → `/var/log/monitor/agent-app/archive/` |
| 삭제 | `archive/*.gz` 중 30일 이상 경과 |
| 예외 처리 | 디렉토리 없음, 권한 부족, 대상 0개 |

## 구현

```bash
find "$AGENT_LOG_DIR" -maxdepth 1 -type f -name '*.log' -mtime +6    # 7일 이상
find "$ARCHIVE_DIR"   -maxdepth 1 -type f -name '*.gz'  -mtime +29   # 30일 이상
```

- `-mtime`은 경과 일수를 버림해서 비교한다. `+6`이 7일 이상이다.
- `gzip`은 원본 수정 시각을 유지한다. 30일 기준이 압축한 날이 아니라 로그가 마지막으로 기록된 날부터 계산된다.
- 같은 이름의 압축본이 아카이브에 있으면 덮어쓰지 않고 건너뛴다.
- 로그와 아카이브는 서로 다른 트리(`/var/log/agent-app`, `/var/log/monitor/agent-app`)에 둔다.

예외 처리 기준:

| 상황 | 처리 |
| --- | --- |
| 아카이브를 만들 수 없거나 쓸 수 없음 | 압축, 삭제 모두 불가하므로 `[ERROR]` 후 exit 1 |
| 로그 디렉토리 없음, 쓰기 권한 없음 | 압축만 건너뛰고 `[WARNING]`, 삭제는 진행 |
| 대상 0개 | `[INFO]` 출력, 정상 종료 |

monitor.sh의 용량 관리와는 기준이 다르다. monitor.sh는 크기(10MB)로 `monitor.log`를 `monitor.<시각>.log`로 넘기고, 이 스크립트는 시간(7일, 30일)으로 그 보관 파일을 압축하고 지운다. `monitor.log`는 매분 기록되므로 7일이 지날 일이 없다.

## 진행

`/var/log`는 root 소유라 아카이브 디렉토리는 미리 만들었다.

```bash
sudo mkdir -p /var/log/monitor/agent-app/archive
sudo chown agent-admin:agent-core /var/log/monitor/agent-app/archive
sudo chmod 2770 /var/log/monitor/agent-app/archive
```

스크립트는 monitor.sh와 같이 agent-dev:agent-core 750으로 배치했다.

## 확인

`touch -d`로 수정 시각을 과거로 바꾼 테스트 파일을 만들어 확인했다.

| 파일 | 수정 시각 | 기대 |
| --- | --- | --- |
| `agent-app/monitor.20260920-030001.log` | 8일 전 | 압축, 이동 |
| `agent-app/recent-test.log` | 3일 전 | 유지 |
| `archive/monitor.20260825-030001.log.gz` | 31일 전 | 삭제 |
| `archive/monitor.20260908-030001.log.gz` | 20일 전 | 유지 |

```
agent-admin@agent-lab:~$ $AGENT_HOME/bin/log-archive.sh; echo "exit code: $?"
[2026-09-28 07:44:00] [INFO] Start (logs: /var/log/agent-app, archive: /var/log/monitor/agent-app/archive)
[2026-09-28 07:44:00] [INFO] Archived: monitor.20260920-030001.log -> /var/log/monitor/agent-app/archive/monitor.20260920-030001.log.gz
[2026-09-28 07:44:00] [INFO] Deleted: monitor.20260825-030001.log.gz
[2026-09-28 07:44:00] [INFO] Done (archived: 1, skipped: 0, deleted: 1)
exit code: 0
```

압축된 파일의 수정 시각은 원본과 같은 2026-09-20이고, `zcat`으로 내용도 확인했다. 테스트 파일은 확인 후 삭제했다.

| 상황 | 재현 | 결과 | 종료 코드 |
| --- | --- | --- | --- |
| 대상 0개 | 한 번 더 실행 | `No logs older than 7 days`, `No archives older than 30 days` | 0 |
| 로그 디렉토리 없음 | `AGENT_LOG_DIR=/nonexistent` | `[WARNING] Log directory not found, skip compression` | 0 |
| 로그 디렉토리 쓰기 권한 없음 | `AGENT_LOG_DIR=/var/log` | `[WARNING] No write permission, skip compression` | 0 |
| 아카이브 생성 불가 | `ARCHIVE_DIR=/root/archive` | `[ERROR] Cannot create archive directory` | 1 |

## cron

```bash
(crontab -l; echo '0 3 * * * /home/agent-admin/agent-app/bin/log-archive.sh >> /var/log/agent-app/log-archive.log 2>&1') | crontab -
```

```
* * * * * /home/agent-admin/agent-app/bin/monitor.sh > /dev/null 2>&1
0 3 * * * /home/agent-admin/agent-app/bin/log-archive.sh >> /var/log/agent-app/log-archive.log 2>&1
```

- 판정 단위가 일 단위라 하루 한 번 실행한다.
- 무엇을 압축하고 지웠는지 남기기 위해 출력은 `log-archive.log`에 누적한다.
- `crontab -`는 목록 전체를 교체하기 때문에 기존 항목을 같이 넘겼다.
