#!/bin/bash
# monitor.sh - agent-app 상태 점검 및 자원 사용률 기록

# cron은 로그인 환경 변수를 읽지 않으므로 기본값을 둔다
AGENT_HOME=${AGENT_HOME:-/home/agent-admin/agent-app}
AGENT_PORT=${AGENT_PORT:-15034}
AGENT_LOG_DIR=${AGENT_LOG_DIR:-/var/log/agent-app}

# 리눅스는 프로세스 이름을 15자까지만 저장한다 (agent-app-linux-arm64 -> agent-app-linux)
APP_NAME=agent-app-linux
LOG_FILE=$AGENT_LOG_DIR/monitor.log
LOG_MAX_BYTES=${LOG_MAX_BYTES:-10485760}   # 10MB
LOG_KEEP=10                                # monitor.log 포함 최대 파일 수

CPU_LIMIT=20
MEM_LIMIT=10
DISK_LIMIT=80

now() {
    date '+%Y-%m-%d %H:%M:%S'
}

# 헬스 체크 실패: 원인을 로그에 남기고 종료
fail() {
    echo "[ERROR] $1"
    echo "[$(now)] ERROR: $1" >> "$LOG_FILE"
    exit 1
}

# $1 > $2 이면 참 (소수점 비교)
over() {
    awk -v value="$1" -v limit="$2" 'BEGIN { exit !(value > limit) }'
}

echo "====== SYSTEM MONITOR RESULT ======"
echo
echo "[HEALTH CHECK]"

# 1. 프로세스: 앱은 부모/자식 2개로 뜨고, 포트를 잡는 쪽은 나중에 뜬 자식
PID=$(pgrep -n -x "$APP_NAME")
if [ -z "$PID" ]; then
    fail "process '$APP_NAME' not running"
fi
echo "Checking process '$APP_NAME'... [OK] (PID: $PID)"

# 2. 포트
if [ -z "$(ss -tlnH "sport = :$AGENT_PORT")" ]; then
    fail "port $AGENT_PORT not listening"
fi
echo "Checking port $AGENT_PORT... [OK]"

# 3. 방화벽: ufw status는 root 전용이라 설정 파일의 활성화 값을 확인
if grep -q '^ENABLED=yes' /etc/ufw/ufw.conf 2>/dev/null; then
    echo "Checking firewall (ufw)... [OK]"
else
    echo "[WARNING] Firewall (ufw) is not active"
fi

# 4. CPU: /proc/stat을 1초 간격으로 두 번 읽어 그 사이 사용률 계산
read -r _ user1 nice1 sys1 idle1 wait1 irq1 soft1 steal1 _ < /proc/stat
sleep 1
read -r _ user2 nice2 sys2 idle2 wait2 irq2 soft2 steal2 _ < /proc/stat
idle=$(( (idle2 + wait2) - (idle1 + wait1) ))
total=$(( (user2 + nice2 + sys2 + idle2 + wait2 + irq2 + soft2 + steal2) \
        - (user1 + nice1 + sys1 + idle1 + wait1 + irq1 + soft1 + steal1) ))
CPU=$(awk -v idle="$idle" -v total="$total" 'BEGIN { printf "%.1f", (total - idle) / total * 100 }')

# 5. 메모리: (전체 - 사용 가능) / 전체
MEM=$(free | awk '/^Mem:/ { printf "%.1f", ($2 - $7) / $2 * 100 }')

# 6. 디스크: 루트 파티션 사용률
DISK=$(df -P / | awk 'NR == 2 { sub("%", "", $5); print $5 }')

echo
echo "[RESOURCE MONITORING]"
echo "CPU Usage : ${CPU}%"
echo "MEM Usage : ${MEM}%"
echo "DISK Used : ${DISK}%"
echo

over "$CPU" "$CPU_LIMIT"   && echo "[WARNING] CPU threshold exceeded (${CPU}% > ${CPU_LIMIT}%)"
over "$MEM" "$MEM_LIMIT"   && echo "[WARNING] MEM threshold exceeded (${MEM}% > ${MEM_LIMIT}%)"
over "$DISK" "$DISK_LIMIT" && echo "[WARNING] DISK threshold exceeded (${DISK}% > ${DISK_LIMIT}%)"

# 7. 로그 용량 관리: 10MB를 넘으면 시각을 붙여 보관하고, monitor.log 포함 10개만 유지
if [ -f "$LOG_FILE" ] && [ "$(stat -c %s "$LOG_FILE")" -ge "$LOG_MAX_BYTES" ]; then
    mv "$LOG_FILE" "$AGENT_LOG_DIR/monitor.$(date '+%Y%m%d-%H%M%S').log"
    ls -1t "$AGENT_LOG_DIR"/monitor.*.log | tail -n +"$LOG_KEEP" | xargs -r rm -f
fi

# 8. 기록
LINE="[$(now)] PID:$PID CPU:${CPU}% MEM:${MEM}% DISK_USED:${DISK}%"
if ! echo "$LINE" >> "$LOG_FILE"; then
    echo "[ERROR] Cannot write $LOG_FILE"
    exit 1
fi
echo
echo "[INFO] Log appended: $LOG_FILE"
