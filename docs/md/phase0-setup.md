# Phase 0. 실습 환경

기록: [log/phase0-install.log](../log/phase0-install.log)

## 목표

맥(Apple Silicon)에서 Ubuntu 22.04 LTS를 띄우고 이후 작업에 필요한 패키지를 설치한다.

## 환경 선택

OrbStack의 Linux machine을 사용했다.

- Docker 컨테이너는 보통 systemd 없이 뜨기 때문에 `systemctl`, ufw, cron을 표준 방식으로 쓰기 어렵다.
- Multipass, Lima 같은 VM 도구는 게스트의 22번 SSH로 셸을 연다. 이 작업에서는 SSH 포트를 바꾸고 방화벽을 켜면 관리 접속이 끊길 수 있다.
- OrbStack machine은 systemd가 정상 동작하고, `orb` 접속이 SSH를 거치지 않아 위 두 문제가 없다.

버전은 22.04로 고정했다. 22.10부터 sshd가 socket activation 방식으로 바뀌어서, 24.04에서는 `sshd_config`의 Port만 바꾸고 재시작해도 22번을 계속 듣는다.

## 진행

```bash
orb create ubuntu:22.04 agent-lab
orb -m agent-lab

sudo apt-get update
sudo apt-get install -y openssh-server ufw acl cron
```

| 패키지 | 사용 |
| --- | --- |
| openssh-server | SSH 포트 변경, root 로그인 차단 |
| ufw | 방화벽 |
| acl | `setfacl`, `getfacl` |
| cron | monitor.sh 주기 실행 (이미지에 기본 포함) |

## 확인

```
$ cat /etc/os-release | head -2
PRETTY_NAME="Ubuntu 22.04.5 LTS"
$ uname -m
aarch64
$ sudo whoami
root
$ systemctl is-active ssh
active
$ systemctl is-active cron
active
$ sudo ufw status
Status: inactive
```

`aarch64`라서 앱 바이너리 중 `agent-app-linux-arm64`를 사용한다.
