#!/bin/bash
# report.sh - monitor.log 통계 (평균, 최대, 최소, 샘플 수)
#
# 사용법: report.sh                                              전체 기간
#         report.sh "2026-09-28 07:00:00" "2026-09-28 08:00:00"  구간 지정

AGENT_LOG_DIR=${AGENT_LOG_DIR:-/var/log/agent-app}
LOG_FILE=${LOG_FILE:-$AGENT_LOG_DIR/monitor.log}
TIME_FORMAT='^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$'

START=$1
END=$2

# 인자는 없거나 2개
if [ $# -ne 0 ] && [ $# -ne 2 ]; then
    echo "Usage: $0 [\"YYYY-MM-DD HH:MM:SS\" \"YYYY-MM-DD HH:MM:SS\"]"
    exit 1
fi

if [ $# -eq 2 ]; then
    if ! [[ $START =~ $TIME_FORMAT && $END =~ $TIME_FORMAT ]]; then
        echo "[ERROR] Time format must be YYYY-MM-DD HH:MM:SS"
        exit 1
    fi
    if [[ $START > $END ]]; then
        echo "[ERROR] Start time is later than end time"
        exit 1
    fi
fi

if [ ! -r "$LOG_FILE" ]; then
    echo "[ERROR] Cannot read $LOG_FILE"
    exit 1
fi

awk -v start="$START" -v end="$END" '
function update(key, value, ts) {
    value += 0
    sum[key] += value
    if (!(key in max) || value > max[key]) { max[key] = value; max_ts[key] = ts }
    if (!(key in min) || value < min[key]) { min[key] = value; min_ts[key] = ts }
}

function show(title, key) {
    printf "  [%s]\n", title
    printf "    Average : %.1f%%\n", sum[key] / n
    printf "    Maximum : %.1f%% at %s\n", max[key], max_ts[key]
    printf "    Minimum : %.1f%% at %s\n", min[key], min_ts[key]
}

# 수치 줄만 사용: [날짜 시각] PID:.. CPU:..% MEM:..% DISK_USED:..%
$4 !~ /^CPU:/ { next }

{
    ts = substr($1, 2) " " substr($2, 1, 8)
    if (start != "" && (ts < start || ts > end)) next

    split($4, cpu, /[:%]/)
    split($5, mem, /[:%]/)
    split($6, disk, /[:%]/)
    update("cpu", cpu[2], ts)
    update("mem", mem[2], ts)
    update("disk", disk[2], ts)

    if (n == 0) first = ts
    last = ts
    n++
}

END {
    if (n == 0) {
        print "[INFO] No samples in the given period"
        exit 1
    }
    print "====== STATISTICS REPORT ======"
    printf "  Period : %s ~ %s\n", first, last
    show("CPU", "cpu")
    show("Memory", "mem")
    show("Disk", "disk")
    print "  [Samples]"
    printf "    Data Points: %d samples\n", n
}
' "$LOG_FILE"
