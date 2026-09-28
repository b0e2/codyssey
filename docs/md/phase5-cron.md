# Phase 5. cron 자동 실행

기록: [log/phase5-cron.log](../log/phase5-cron.log)

## 목표

- agent-admin crontab으로 monitor.sh 매분 실행
- 1~2분 안에 monitor.log가 자동으로 늘어나는지 확인

## 진행

```bash
sudo -iu agent-admin
echo '* * * * * /home/agent-admin/agent-app/bin/monitor.sh > /dev/null 2>&1' | crontab -
crontab -l
```

- cron에는 `$AGENT_HOME`이 없어서 절대 경로로 적었다.
- 화면 출력은 버렸다. 필요한 기록(수치, 실패 원인)은 monitor.sh가 monitor.log에 직접 남긴다.
- root가 아닌 agent-admin crontab에 등록했다. monitor.sh는 agent-core 그룹 권한으로 실행된다.

등록 전에 `env -i PATH=/usr/bin:/bin`으로 환경 변수를 비운 상태에서 monitor.sh를 실행해 cron 환경에서도 동작하는지 확인했다.

## 확인

```
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
```

대기하는 동안 직접 실행하지 않았는데 07:36, 07:37에 한 줄씩 늘었다. 기록 시각이 :02인 것은 cron이 0초 무렵 시작하고 CPU를 1초 동안 측정하기 때문이다.

```
$ sudo grep 'CRON.*agent-admin' /var/log/syslog | tail -3
Sep 28 07:36:01 agent-lab CRON[7525]: (agent-admin) CMD (/home/agent-admin/agent-app/bin/monitor.sh > /dev/null 2>&1)
Sep 28 07:37:01 agent-lab CRON[7544]: (agent-admin) CMD (/home/agent-admin/agent-app/bin/monitor.sh > /dev/null 2>&1)
```

syslog에서 agent-admin 계정으로 실행된 기록도 확인했다.
