#!/bin/bash
# log-archive.sh - 오래된 로그 압축, 보관, 삭제
#
#   7일 지난 $AGENT_LOG_DIR/*.log  -> gzip 압축 후 아카이브로 이동
#   30일 지난 아카이브 *.gz        -> 삭제

AGENT_LOG_DIR=${AGENT_LOG_DIR:-/var/log/agent-app}
ARCHIVE_DIR=${ARCHIVE_DIR:-/var/log/monitor/agent-app/archive}

now() {
    date '+%Y-%m-%d %H:%M:%S'
}

log() {
    echo "[$(now)] $*"
}

found=0
archived=0
skipped=0
deleted=0

log "[INFO] Start (logs: $AGENT_LOG_DIR, archive: $ARCHIVE_DIR)"

# 1. 아카이브 디렉토리: 없으면 만들고, 만들 수 없거나 쓸 수 없으면 중단
if [ ! -d "$ARCHIVE_DIR" ] && ! mkdir -p "$ARCHIVE_DIR" 2>/dev/null; then
    log "[ERROR] Cannot create archive directory: $ARCHIVE_DIR"
    exit 1
fi
if [ ! -w "$ARCHIVE_DIR" ]; then
    log "[ERROR] No write permission: $ARCHIVE_DIR"
    exit 1
fi

# 2. 압축, 이동: 로그 디렉토리가 없거나 권한이 없으면 이 단계만 건너뜀
if [ ! -d "$AGENT_LOG_DIR" ]; then
    log "[WARNING] Log directory not found, skip compression: $AGENT_LOG_DIR"
elif [ ! -w "$AGENT_LOG_DIR" ]; then
    log "[WARNING] No write permission, skip compression: $AGENT_LOG_DIR"
else
    # -mtime +6: 수정된 지 7일 이상
    while read -r file; do
        found=$((found + 1))
        name=$(basename "$file")
        if [ -e "$ARCHIVE_DIR/$name.gz" ]; then
            log "[WARNING] Already archived, skip: $name"
            skipped=$((skipped + 1))
            continue
        fi
        if gzip "$file" && mv "$file.gz" "$ARCHIVE_DIR/"; then
            log "[INFO] Archived: $name -> $ARCHIVE_DIR/$name.gz"
            archived=$((archived + 1))
        else
            log "[WARNING] Failed to archive: $name"
        fi
    done < <(find "$AGENT_LOG_DIR" -maxdepth 1 -type f -name '*.log' -mtime +6)

    [ "$found" -eq 0 ] && log "[INFO] No logs older than 7 days"
fi

# 3. 삭제: -mtime +29 = 수정된 지 30일 이상
while read -r file; do
    if rm -f "$file"; then
        log "[INFO] Deleted: $(basename "$file")"
        deleted=$((deleted + 1))
    else
        log "[WARNING] Failed to delete: $(basename "$file")"
    fi
done < <(find "$ARCHIVE_DIR" -maxdepth 1 -type f -name '*.gz' -mtime +29)

[ "$deleted" -eq 0 ] && log "[INFO] No archives older than 30 days"

log "[INFO] Done (archived: $archived, skipped: $skipped, deleted: $deleted)"
