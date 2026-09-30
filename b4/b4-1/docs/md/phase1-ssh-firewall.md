# Phase 1. SSH, 방화벽

기록: [log/phase1-ssh-firewall.log](../log/phase1-ssh-firewall.log)

## 목표

- SSH 포트 20022 변경
- root 원격 로그인 차단
- UFW 활성화, 인바운드는 20022/tcp, 15034/tcp만 허용

## 진행

### SSH

기본 설정 파일에는 `#Port 22`, `#PermitRootLogin prohibit-password`처럼 주석 처리된 기본값이 있다. 이 줄을 sed로 교체했다.

```bash
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak
sudo sed -i 's/^#\?Port .*/Port 20022/' /etc/ssh/sshd_config
sudo sed -i 's/^#\?PermitRootLogin .*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sshd -t && echo "문법 OK"
sudo systemctl restart ssh
```

재시작 전에 `sshd -t`로 문법을 먼저 검사했다. 설정이 깨진 상태로 재시작하면 sshd가 올라오지 않고, 원격 서버였다면 접속 수단이 없어진다.

### 방화벽

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 20022/tcp
sudo ufw allow 15034/tcp
sudo ufw enable
```

들어오는 연결은 기본 차단하고 필요한 포트만 열었다. `/tcp`를 붙이지 않으면 UDP까지 같이 열린다.
SSH 허용 규칙을 먼저 추가한 뒤 `enable` 했다. 순서가 바뀌면 SSH로 접속 중인 경우 켜는 순간 연결이 끊긴다.

## 확인

```
$ grep -nE '^(Port|PermitRootLogin) ' /etc/ssh/sshd_config
14:Port 20022
33:PermitRootLogin no

$ sudo ss -tlnp | grep sshd
LISTEN 0      128          0.0.0.0:20022      0.0.0.0:*    users:(("sshd",pid=3292,fd=3))
LISTEN 0      128             [::]:20022         [::]:*    users:(("sshd",pid=3292,fd=4))

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

설정 파일 값과 실제 LISTEN 포트를 둘 다 확인했다. `(v6)`는 같은 규칙의 IPv6 버전이다.

## 정리

- 포트 변경은 22번을 노리는 자동 스캔과 무작위 로그인 시도를 줄인다. 포트 스캔으로 찾을 수는 있어서 근본적인 방어는 아니다.
- root는 모든 리눅스에 있는 계정이라 이름을 추측할 필요가 없다. 차단하면 일반 계정으로 로그인한 뒤 sudo를 거쳐야 하고, sudo 사용 기록도 남는다.
