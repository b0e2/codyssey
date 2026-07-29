# 포트 충돌 진단 및 해결

포트 매핑 실습(05) 중, 이미 사용 중인 호스트 포트로 컨테이너를 실행하면 어떤 일이 벌어지는지와 그 진단·해결 절차를 정리한다. 진단 흐름은 **포트 확인 → 프로세스 확인 → 포트 변경** 순서다.

## 1. 문제 재현 (포트 충돌 발생)

먼저 컨테이너 A가 호스트 8080 포트를 점유하도록 실행한 뒤, 같은 8080으로 컨테이너 B를 띄워본다.

```
$ docker run -d -p 8080:80 --name port-a alpine sleep 300
5c1e0d3f... (port-a 실행됨, 호스트 8080 점유)

$ docker run -d -p 8080:80 --name port-b alpine sleep 300
091ae55282a1...
docker: Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint port-b: Bind for 0.0.0.0:8080 failed: port is already allocated
```

**원인 가설**: 컨테이너 B가 실패한 이유는 컨테이너 내부(80)가 아니라, 매핑 대상인 **호스트 포트 8080이 이미 다른 프로세스에 의해 점유**되어 있기 때문이다.

## 2. 어떤 프로세스가 포트를 쓰는지 확인 (lsof)

호스트에서 8080을 누가 LISTEN 중인지 `lsof`로 조회한다. (Linux에서는 `ss -ltnp 'sport = :8080'` 또는 `sudo lsof -i :8080`을 사용할 수 있다.)

```
$ lsof -nP -i :8080
COMMAND     PID           USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
OrbStack  52231  beenjeong0****  121u  IPv4 0x6d9e9b6b0a158e99      0t0  TCP *:8080 (LISTEN)
OrbStack  52231  beenjeong0****  122u  IPv6 0xd90aaba80d320865      0t0  TCP *:8080 (LISTEN)
```

컨테이너 A의 포트 매핑을 Docker 엔진(OrbStack)이 호스트 8080에 바인딩해 LISTEN 중임을 확인했다. 즉, 8080은 사용 불가 상태다.

## 3. 해결: 비어 있는 호스트 포트로 변경

컨테이너 내부 포트(80)는 그대로 두고, 매핑의 **왼쪽(호스트) 값만** 비어 있는 8082로 바꿔 재실행한다.

```
$ docker rm port-b
port-b

$ docker run -d -p 8082:80 --name port-b alpine sleep 300
7f2a9c... (port-b 실행됨, 호스트 8082)

$ docker ps --filter name=port- --format 'table {{.Names}}\t{{.Ports}}\t{{.Status}}'
NAMES     PORTS                                     STATUS
port-b    0.0.0.0:8082->80/tcp, [::]:8082->80/tcp   Up Less than a second
port-a    0.0.0.0:8080->80/tcp, [::]:8080->80/tcp   Up Less than a second
```

**해결 결과**: 호스트 포트를 8082로 바꾸자 두 컨테이너가 각각 8080·8082에서 정상 동작했다.

## 확인한 항목

- 포트 충돌은 컨테이너 내부 포트가 아니라 **호스트 포트**에서 발생함을 확인
- 진단 절차: `docker run` 실패 메시지 → `lsof -nP -i :<port>`로 점유 프로세스 확인 → 매핑의 호스트 포트만 변경
- `-p <host>:<container>`에서 왼쪽(host) 값만 바꾸면 충돌을 회피할 수 있음
