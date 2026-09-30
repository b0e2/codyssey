#!/bin/bash
# monitor.sh - agent-leak-app 프로세스 자원 사용률 기록

AGENT_LOG_DIR=${AGENT_LOG_DIR:-/var/log/agent-app}

# 리눅스는 프로세스 이름을 15자까지만 저장한다 (agent-leak-app-arm64 -> agent-leak-app-)
APP_NAME=agent-leak-app-
LOG_FILE=$AGENT_LOG_DIR/monitor.log
APP_LOG=$AGENT_LOG_DIR/agent_app.log

# CPU 측정 구간(초). 앱의 작업 주기(약 3초)보다 짧으면 순간 부하를 놓친다
SAMPLE_SEC=${SAMPLE_SEC:-3}

now() {
    date '+%Y-%m-%d %H:%M:%S'
}

record() {
    echo "[$(now)] $1" | tee -a "$LOG_FILE"
}

# 앱은 부모/자식 2개로 뜨고, 실제로 일하는 쪽은 나중에 뜬 자식
PID=$(pgrep -n -x "$APP_NAME")
if [ -z "$PID" ]; then
    record "PROCESS:down"
    exit 1
fi

# CPU: SAMPLE_SEC 동안 시스템 전체와 프로세스가 사용한 CPU 시간을 같이 측정
read -r _ u1 n1 s1 i1 w1 q1 sq1 st1 _ < /proc/stat
p1=$(awk '{ print $14 + $15 }' "/proc/$PID/stat" 2>/dev/null)
sleep "$SAMPLE_SEC"
read -r _ u2 n2 s2 i2 w2 q2 sq2 st2 _ < /proc/stat
p2=$(awk '{ print $14 + $15 }' "/proc/$PID/stat" 2>/dev/null)
if [ -z "$p1" ] || [ -z "$p2" ]; then
    record "PROCESS:down"
    exit 1
fi

idle=$(( (i2 + w2) - (i1 + w1) ))
total=$(( (u2 + n2 + s2 + i2 + w2 + q2 + sq2 + st2) - (u1 + n1 + s1 + i1 + w1 + q1 + sq1 + st1) ))
SYS_CPU=$(awk -v idle="$idle" -v total="$total" 'BEGIN { printf "%.1f", (total - idle) / total * 100 }')

# 프로세스 CPU는 top과 같은 기준 (코어 1개 = 100%)
PROC_CPU=$(awk -v used=$(( p2 - p1 )) -v hz="$(getconf CLK_TCK)" -v sec="$SAMPLE_SEC" 'BEGIN { printf "%.1f", used / hz / sec * 100 }')

# 메모리: 프로세스 실제 사용량(RSS)과 시스템 전체 사용률
read -r STATE THREADS RSS_KB < <(awk '/^State:/ { s = $2 } /^Threads:/ { t = $2 } /^VmRSS:/ { r = $2 } END { print s, t, r }' "/proc/$PID/status")
MEM_TOTAL_KB=$(awk '/^MemTotal:/ { print $2 }' /proc/meminfo)
RSS_MB=$(( RSS_KB / 1024 ))
PROC_MEM=$(awk -v rss="$RSS_KB" -v total="$MEM_TOTAL_KB" 'BEGIN { printf "%.1f", rss / total * 100 }')
SYS_MEM=$(free | awk '/^Mem:/ { printf "%.1f", ($2 - $7) / $2 * 100 }')

# 앱 로그가 마지막으로 기록된 뒤 지난 시간 (멈춤 여부 확인용)
LOG_IDLE=$(( $(date +%s) - $(stat -c %Y "$APP_LOG" 2>/dev/null || date +%s) ))

record "PID:$PID STAT:$STATE THREADS:$THREADS CPU:${PROC_CPU}% RSS:${RSS_MB}MB MEM:${PROC_MEM}% SYS_CPU:${SYS_CPU}% SYS_MEM:${SYS_MEM}% LOG_IDLE:${LOG_IDLE}s"
