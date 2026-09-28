# Phase 3. 앱 실행 환경

기록: [log/phase3-app-env.log](../log/phase3-app-env.log)

## 목표

- 환경 변수 5개 설정
- 키 파일 생성
- agent-admin 계정으로 앱 실행, Boot Sequence 5단계 [OK]와 Agent READY
- `0.0.0.0:15034` LISTEN

## 명세와 앱의 차이

명세 값 그대로 설정했을 때 앱이 부팅에 실패했다. 앱이 출력한 메시지로 기대값을 확인했다.

| 항목 | 명세 | 앱 요구 | 앱 메시지 |
| --- | --- | --- | --- |
| `AGENT_KEY_PATH` | `$AGENT_HOME/api_keys/t_secret.key` | `$AGENT_HOME/api_keys` | `Key Path Mismatch. Expected: /home/agent-admin/agent-app/api_keys` |
| 키 파일 이름 | `t_secret.key` | `secret.key` | `Missing File: secret.key` |

arm64, x86 바이너리의 날짜가 달라(5/18, 5/20) 버전 차이일 수 있다고 보고 x86 바이너리도 amd64 머신에서 실행해 봤다. 결과는 같았다.

성공 기준이 Boot 5단계 통과라서 앱 요구에 맞췄다.

- `AGENT_KEY_PATH`는 디렉토리 경로로 설정
- 키 파일은 명세대로 `t_secret.key`로 만들고, `secret.key`는 이 파일을 가리키는 심볼릭 링크로 두었다. 키 원본은 하나만 관리한다.

## 진행

### 앱 배치

```bash
sudo apt-get install -y unzip
unzip -o /Users/jeongbin/Downloads/agent-app.zip agent-app-linux-arm64 -d /tmp
sudo cp /tmp/agent-app-linux-arm64 /home/agent-admin/agent-app/
sudo chown agent-admin:agent-core /home/agent-admin/agent-app/agent-app-linux-arm64
sudo chmod 750 /home/agent-admin/agent-app/agent-app-linux-arm64
```

zip 안의 파일에 실행 권한이 없어서 750을 줬다.

### 키 파일

```bash
echo 'agent_api_key_test' | sudo tee /home/agent-admin/agent-app/api_keys/t_secret.key
sudo chown agent-admin:agent-core /home/agent-admin/agent-app/api_keys/t_secret.key
sudo ln -s t_secret.key /home/agent-admin/agent-app/api_keys/secret.key
sudo chown -h agent-admin:agent-core /home/agent-admin/agent-app/api_keys/secret.key
```

```
lrwxrwxrwx  1 agent-admin agent-core 12 Sep 28 07:16 secret.key -> t_secret.key
-rw-rw----+ 1 agent-admin agent-core 19 Sep 28 07:16 t_secret.key
```

### 환경 변수

```bash
sudo tee /etc/profile.d/agent-app.sh <<'EOF'
export AGENT_HOME=/home/agent-admin/agent-app
export AGENT_PORT=15034
export AGENT_UPLOAD_DIR=$AGENT_HOME/upload_files
export AGENT_KEY_PATH=$AGENT_HOME/api_keys
export AGENT_LOG_DIR=/var/log/agent-app
EOF
```

`/etc/profile.d`는 모든 계정의 로그인 셸에서 읽힌다. agent-admin의 `.bashrc`에 넣으면 agent-dev가 테스트할 때 변수가 없고, `/etc/environment`는 `$AGENT_HOME` 같은 변수 참조를 쓸 수 없다.
cron은 로그인 셸이 아니라 이 파일을 읽지 않는다. monitor.sh에서 따로 처리했다.

### 실행

```bash
sudo -iu agent-admin
env | grep ^AGENT_ | sort
$AGENT_HOME/agent-app-linux-arm64
```

`-i`로 로그인 셸을 열어야 profile.d가 적용된다. Boot Sequence를 확인한 뒤 Ctrl+C로 종료하고, 모니터링 대상이 되도록 백그라운드로 다시 실행했다.

```bash
nohup $AGENT_HOME/agent-app-linux-arm64 > /dev/null 2>&1 &
```

앱이 `/var/log/agent-app/agent_app.log`에 직접 기록하기 때문에 표준 출력은 저장하지 않았다.

## 확인

```
AGENT_HOME=/home/agent-admin/agent-app
AGENT_KEY_PATH=/home/agent-admin/agent-app/api_keys
AGENT_LOG_DIR=/var/log/agent-app
AGENT_PORT=15034
AGENT_UPLOAD_DIR=/home/agent-admin/agent-app/upload_files

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

- 실행 계정은 agent-admin이다.
- 앱은 PyInstaller로 만들어져 부모/자식 프로세스 2개로 뜬다. 15034를 연 것은 자식(4272)이다.
- 부팅 후 앱은 CPU와 메모리 사용량을 주기적으로 올렸다 내린다(최대 256MB).

머신을 재시작하면 앱이 꺼지므로 다시 실행해야 한다.
