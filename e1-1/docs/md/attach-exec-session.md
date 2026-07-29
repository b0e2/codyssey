# 컨테이너 종료/유지 (attach vs exec) 차이 관찰

## 목적

이미 실행 중인 컨테이너에 다시 접속하는 두 가지 방법(`docker exec`, `docker attach`)이 컨테이너의 생명주기에 어떤 영향을 주는지 직접 비교한다.

## 수행 명령 및 결과

```
$ docker run -d --name test-nginx nginx
c05a023103d3c5478a9fb6bfbb8a2f81bae16fdb9114fef3713684c2204fb736

$ docker ps
CONTAINER ID   IMAGE   COMMAND                  CREATED         STATUS         PORTS    NAMES
c05a023103d3   nginx   "/docker-entrypoint.…"   5 seconds ago   Up 4 seconds   80/tcp   test-nginx
```

### exec으로 접속 후 종료

```
$ docker exec -it test-nginx bash
root@c05a023103d3:/# ls
bin   docker-entrypoint.d   home   media  proc  sbin  tmp
boot  docker-entrypoint.sh  lib    mnt    root   srv   usr
dev   etc                   lib64  opt    run    sys   var
root@c05a023103d3:/# exit
exit

$ docker ps
CONTAINER ID   IMAGE   COMMAND                  CREATED          STATUS          PORTS    NAMES
c05a023103d3   nginx   "/docker-entrypoint.…"   33 seconds ago   Up 31 seconds   80/tcp   test-nginx
```

**결과**: `exec`으로 들어간 bash 셸에서 `exit`을 실행해도, 컨테이너의 메인 프로세스(nginx)는 영향받지 않아 컨테이너가 계속 `Up` 상태로 유지된다.

### attach로 접속 후 종료

```
$ docker attach test-nginx
^C2026/07/28 08:35:52 [notice] 1#1: signal 2 (SIGINT) received, exiting
2026/07/28 08:35:52 [notice] 30#30: exiting
2026/07/28 08:35:52 [notice] 32#32: exiting
2026/07/28 08:35:52 [notice] 1#1: worker process 32 exited with code 0
2026/07/28 08:35:52 [notice] 1#1: worker process 29 exited with code 0
2026/07/28 08:35:52 [notice] 1#1: worker process 31 exited with code 0
2026/07/28 08:35:52 [notice] 1#1: worker process 33 exited with code 0
2026/07/28 08:35:52 [notice] 1#1: worker process 30 exited with code 0
2026/07/28 08:35:52 [notice] 1#1: worker process 34 exited with code 0
2026/07/28 08:35:52 [notice] 1#1: exit

$ docker ps
CONTAINER ID   IMAGE        COMMAND                  CREATED          STATUS                    PORTS                                         NAMES
6dfc7648cc9c   my-web:1.0   "uvicorn main:app --…"   52 minutes ago   Up 52 minutes (healthy)   0.0.0.0:8081->8000/tcp, [::]:8081->8000/tcp   my-web-8081
543e358c6a37   my-web:1.0   "uvicorn main:app --…"   52 minutes ago   Up 52 minutes (healthy)   0.0.0.0:8080->8000/tcp, [::]:8080->8000/tcp   my-web-8080
```

**결과**: `attach`로 컨테이너의 메인 프로세스(PID 1, nginx 마스터)에 직접 연결된 상태에서 `Ctrl+C`(SIGINT)를 보내자, nginx 마스터 프로세스와 모든 워커 프로세스가 종료되었다. 메인 프로세스가 죽으면서 컨테이너 자체가 종료(Exited)되어 `docker ps` 목록에서 완전히 사라졌다.

## 정리

```
$ docker rm test-nginx
test-nginx
```

## 개념 정리

| 구분 | exec | attach |
|---|---|---|
| 연결 대상 | 새로운 프로세스(별도 셸)를 추가로 실행 | 컨테이너의 메인 프로세스(PID 1)에 직접 연결 |
| 종료 시 영향 | 새로 띄운 프로세스만 종료, 컨테이너는 계속 실행 | 메인 프로세스가 종료되어 컨테이너 자체가 종료됨 |
| 실무 활용 | 실행 중인 컨테이너 내부를 잠깐 들여다볼 때 | 메인 프로세스의 표준 입출력에 직접 개입해야 할 때 |

`exec`은 컨테이너 안에 새 창을 하나 더 여는 것과 비슷하고, `attach`는 이미 켜져 있는 화면에 다시 이어 붙는 것과 비슷하다. 그래서 `attach` 상태에서 `Ctrl+C`나 `exit`을 잘못 입력하면 서비스 자체가 죽을 수 있어, 운영 중인 컨테이너를 들여다볼 때는 `exec`을 사용하는 것이 안전하다.

## 확인한 항목

- `exec`으로 접속 후 종료 시 컨테이너 유지 확인
- `attach`로 접속 후 `Ctrl+C` 시 컨테이너 종료 확인
- 두 방식의 차이를 실행 결과로 직접 관찰 및 정리