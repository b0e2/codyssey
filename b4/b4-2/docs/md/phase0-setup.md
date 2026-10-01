# Phase 0. 실습 환경 구성

기록: [phase0-setup.log](../log/phase0-setup.log)

## 목표

- 다른 서비스와 분리된 리눅스 환경에서 agent-leak-app 실행
- 관제에 필요한 도구 설치

## 진행

```bash
orb create ubuntu:22.04 leak-lab
orb list
orb -m leak-lab
head -2 /etc/os-release
uname -m
sudo apt-get update
sudo apt-get install -y unzip htop bsdextrautils
unzip -o /Users/jeongbin/Downloads/agent-app-leak.zip agent-leak-app-arm64 -d /tmp
ls -l /tmp/agent-leak-app-arm64
```

- OrbStack Linux machine을 새로 만들어 기존 머신과 포트, 프로세스가 섞이지 않게 했습니다.
- `ps`, `top`, `pstree`, `kill`은 기본 설치되어 있어 `htop`만 추가했습니다.

## 확인

```
NAME       STATE    DISTRO  VERSION  ARCH   SIZE      IP
leak-lab   running  ubuntu  jammy    arm64  717.6 MB  192.168.139.235

PRETTY_NAME="Ubuntu 22.04.5 LTS"
aarch64

-rwxr-xr-x 1 jeongbin jeongbin 6261928 May 26 11:04 /tmp/agent-leak-app-arm64
```

| 항목 | 결과 |
| --- | --- |
| OS | Ubuntu 22.04.5 LTS |
| 아키텍처 | aarch64 → `agent-leak-app-arm64` 사용 |
| 앱 파일 | 6.2MB, 실행 권한 있음 |
