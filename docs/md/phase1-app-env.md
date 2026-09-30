# Phase 1. 앱 실행 환경 구성

기록: [phase1-app-env.log](../log/phase1-app-env.log)

## 목표

- root가 아닌 일반 계정으로 앱 실행
- 실행에 필요한 디렉터리, 키 파일, 환경 변수 구성
- 부팅 검사 통과, `0.0.0.0:15034` 바인딩 확인

## 진행

### 실행 계정, 로그 디렉터리

```bash
sudo useradd -m -s /bin/bash agent-admin
sudo mkdir -p /var/log/agent-app
sudo chown agent-admin:agent-admin /var/log/agent-app
```

### 앱 파일, 키 파일

```bash
unzip -o /Users/jeongbin/Downloads/agent-app-leak.zip agent-leak-app-arm64 -d /tmp
sudo -iu agent-admin
mkdir -p ~/agent-app/upload_files ~/agent-app/api_keys
cp /tmp/agent-leak-app-arm64 ~/agent-app/
echo 'agent_api_key_test' > ~/agent-app/api_keys/secret.key
```

### 환경 변수

```bash
cat > ~/.bash_profile <<'EOF'
export AGENT_HOME=$HOME/agent-app
export AGENT_PORT=15034
export AGENT_UPLOAD_DIR=$AGENT_HOME/upload_files
export AGENT_KEY_PATH=$AGENT_HOME/api_keys
export AGENT_LOG_DIR=/var/log/agent-app
export MEMORY_LIMIT=512
export CPU_MAX_OCCUPY=30
export MULTI_THREAD_ENABLE=false
EOF
```

- 실행 계정이 하나라서 `~agent-admin/.bash_profile`에 두었습니다.
- 이후 장애 재현에서는 이 파일의 `MEMORY_LIMIT`, `CPU_MAX_OCCUPY`, `MULTI_THREAD_ENABLE` 중 하나만 바꿉니다.

### 실행

```bash
nohup $AGENT_HOME/agent-leak-app-arm64 > $AGENT_LOG_DIR/console.log 2>&1 &
head -40 $AGENT_LOG_DIR/console.log
ss -tlnp | grep 15034
ps -o user,pid,ppid,ni,stat,cmd -u agent-admin
kill %1
```

## 확인

```
[1/6] Checking User Account               [OK]
   ... Running as service user 'agent-admin' (uid=1000)
[2/6] Verifying Environment Variables     [OK]
[3/6] Checking Required Files             [OK]
[4/6] Checking Port Availability          [OK]
[5/6] Verifying Log Permission            [OK]
[6/6] Verifying Mission Environment       [OK]
   ... MEMORY_LIMIT=512MB, CPU_MAX_OCCUPY=30%, MULTI_THREAD_ENABLE=False
All Boot Checks Passed!
Agent READY
```

```
LISTEN 0      1            0.0.0.0:15034      0.0.0.0:*    users:(("agent-leak-app-",pid=775,fd=4))

USER         PID    PPID  NI STAT CMD
agent-a+     774     765   0 S    /home/agent-admin/agent-app/agent-leak-app-arm64
agent-a+     775     774  10 SNl  /home/agent-admin/agent-app/agent-leak-app-arm64
```

- 부모(774)와 자식(775) 2개로 실행되고, 포트를 잡는 쪽은 자식입니다.
- 자식은 스스로 nice 10으로 우선순위를 낮춥니다 (`SafetyGuard`).
- 프로세스 이름은 15자로 잘려 `agent-leak-app-`로 표시됩니다.

## 설정값별 동작

기본값에서 한 값씩 바꿔 실행해 본 결과입니다.

| 설정 | Resource Check | 동작 |
| --- | --- | --- |
| `MEMORY_LIMIT` 256 이하 | `WARNING: Recommend Over 256MB` | 메모리 증가 후 `SELF-TERMINATED` |
| `CPU_MAX_OCCUPY` 50 초과 | `WARNING: Recommend Under 50%` | 부하 증가 후 `WATCHDOG ... SIGTERM` |
| `MULTI_THREAD_ENABLE=true` | `POTENTIAL DEADLOCK IN CONCURRENT MODE` | 로그 정지, 프로세스 유지 |
| 512 / 30 / false | 모두 `OK` | 정상 동작 |

- Ctrl+C는 한 번에 종료되지 않아 종료는 `kill`, `pkill`을 사용했습니다.
