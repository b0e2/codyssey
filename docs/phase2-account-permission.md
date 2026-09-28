# Phase 2. 계정, 그룹, 디렉토리 권한

기록: [sessions/phase2-account-permission.log](sessions/phase2-account-permission.log)

## 목표

| 대상 | 접근 가능 | 권한 |
| --- | --- | --- |
| `$AGENT_HOME/upload_files` | agent-common (admin, dev, test) | 읽기/쓰기 |
| `$AGENT_HOME/api_keys` | agent-core (admin, dev) | 읽기/쓰기 |
| `/var/log/agent-app` | agent-core (admin, dev) | 읽기/쓰기 |

agent-test는 업로드 파일은 다루지만 키와 운영 로그에는 접근하지 못하게 한다.

## 진행

### 계정, 그룹

```bash
sudo groupadd agent-common
sudo groupadd agent-core
sudo useradd -m -s /bin/bash -G agent-common,agent-core agent-admin
sudo useradd -m -s /bin/bash -G agent-common,agent-core agent-dev
sudo useradd -m -s /bin/bash -G agent-common agent-test
```

### 디렉토리, 권한

```bash
sudo mkdir -p /home/agent-admin/agent-app/upload_files
sudo mkdir -p /home/agent-admin/agent-app/api_keys
sudo mkdir -p /var/log/agent-app

sudo chown agent-admin:agent-common /home/agent-admin/agent-app
sudo chmod 750 /home/agent-admin/agent-app
sudo chown agent-admin:agent-common /home/agent-admin/agent-app/upload_files
sudo chmod 2770 /home/agent-admin/agent-app/upload_files
sudo chown agent-admin:agent-core /home/agent-admin/agent-app/api_keys
sudo chmod 2770 /home/agent-admin/agent-app/api_keys
sudo chown agent-admin:agent-core /var/log/agent-app
sudo chmod 2770 /var/log/agent-app
```

기타 권한을 0으로 두어 그룹에 속하지 않은 계정은 접근할 수 없게 했다.

### ACL

```bash
sudo setfacl -m g:agent-common:x /home/agent-admin
sudo setfacl -d -m g:agent-common:rwx /home/agent-admin/agent-app/upload_files
sudo setfacl -d -m g:agent-core:rwx /home/agent-admin/agent-app/api_keys
sudo setfacl -d -m g:agent-core:rwx /var/log/agent-app
```

권한만으로 해결되지 않는 부분이 두 가지 있었다.

1. Ubuntu 22.04는 새 홈 디렉토리를 750으로 만든다(`HOME_MODE 0750`). agent-dev, agent-test는 `/home/agent-admin`을 지나갈 수 없어서 그 안의 `upload_files`에 도달하지 못한다. agent-common에 통과(x) 권한만 추가했다. 목록 보기(r)는 주지 않았다.
2. setgid(`2770`의 2)로 새 파일의 그룹은 폴더 그룹을 따라가지만, 파일 권한은 만든 사람의 umask(022)를 따라 644가 된다. 다른 그룹원이 수정할 수 없어서 default ACL로 그룹 쓰기 권한을 상속시켰다.

## 확인

```
$ id agent-admin
uid=1000(agent-admin) gid=1002(agent-admin) groups=1002(agent-admin),1000(agent-common),1001(agent-core)
$ id agent-dev
uid=1001(agent-dev) gid=1003(agent-dev) groups=1003(agent-dev),1000(agent-common),1001(agent-core)
$ id agent-test
uid=1002(agent-test) gid=1004(agent-test) groups=1004(agent-test),1000(agent-common)

$ sudo ls -ld /home/agent-admin /home/agent-admin/agent-app /home/agent-admin/agent-app/upload_files /home/agent-admin/agent-app/api_keys /var/log/agent-app
drwxr-x---+ 1 agent-admin agent-admin  72 Sep 28 07:09 /home/agent-admin
drwxr-x---  1 agent-admin agent-common 40 Sep 28 07:09 /home/agent-admin/agent-app
drwxrws---+ 1 agent-admin agent-core    0 Sep 28 07:09 /home/agent-admin/agent-app/api_keys
drwxrws---+ 1 agent-admin agent-common  0 Sep 28 07:09 /home/agent-admin/agent-app/upload_files
drwxrws---+ 1 agent-admin agent-core    0 Sep 28 07:09 /var/log/agent-app

$ sudo getfacl -p /home/agent-admin/agent-app/upload_files
# file: /home/agent-admin/agent-app/upload_files
# owner: agent-admin
# group: agent-common
# flags: -s-
user::rwx
group::rwx
other::---
default:user::rwx
default:group::rwx
default:group:agent-common:rwx
default:mask::rwx
default:other::---
```

설정 값과 별개로 계정별로 직접 접근해 봤다.

```bash
sudo -u agent-test touch /home/agent-admin/agent-app/upload_files/test.txt
sudo -u agent-dev bash -c 'echo dev >> /home/agent-admin/agent-app/upload_files/test.txt'
sudo -u agent-test ls /home/agent-admin/agent-app/api_keys
sudo -u agent-test touch /var/log/agent-app/test.log
sudo -u agent-dev touch /var/log/agent-app/test.log
```

| 테스트 | 결과 |
| --- | --- |
| agent-test → upload_files 파일 생성 | 성공 |
| agent-dev → agent-test가 만든 파일 수정 | 성공 (`-rw-rw----+ agent-test agent-common`) |
| agent-test → api_keys 목록 | Permission denied |
| agent-test → /var/log/agent-app 쓰기 | Permission denied |
| agent-dev → /var/log/agent-app 쓰기 | 성공 |
| agent-test → /home/agent-admin 목록 | Permission denied |

`sudo -u agent-dev echo dev >> 파일`로 쓰면 `>>`는 현재 셸 권한으로 처리된다. 그래서 `bash -c`로 감싸 리다이렉션까지 agent-dev 권한으로 실행했다.
