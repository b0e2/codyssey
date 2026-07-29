# Docker 기본 운영 명령 및 컨테이너 실습

## 수행 명령 및 결과

```
$ docker images
REPOSITORY   TAG       IMAGE ID   CREATED   SIZE

$ docker ps
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES

$ docker ps -a
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES

$ docker run hello-world
Unable to find image 'hello-world:latest' locally
latest: Pulling from library/hello-world
Status: Downloaded newer image for hello-world:latest

Hello from Docker!
This message shows that your installation appears to be working correctly.

$ docker images
REPOSITORY    TAG       IMAGE ID       CREATED        SIZE
hello-world   latest    e2ac70e7319a   4 months ago   10.1kB

$ docker ps -a
CONTAINER ID   IMAGE         COMMAND    CREATED          STATUS                      PORTS     NAMES
a09fc5b98b54   hello-world   "/hello"   14 seconds ago   Exited (0) 13 seconds ago             eager_driscoll

$ docker logs a09fc5b98b54
Hello from Docker!
This message shows that your installation appears to be working correctly.

$ docker run -it ubuntu bash
Unable to find image 'ubuntu:latest' locally
latest: Pulling from library/ubuntu
Status: Downloaded newer image for ubuntu:latest

root@cec7c58bcad3:/# ls
bin  boot  dev  etc  home  lib  lib64  media  mnt  opt  proc  root  run  sbin  srv  sys  tmp  usr  var

root@cec7c58bcad3:/# echo "hello from container"
hello from container

root@cec7c58bcad3:/# exit
exit

$ docker ps -a
CONTAINER ID   IMAGE         COMMAND    CREATED          STATUS                     PORTS     NAMES
cec7c58bcad3   ubuntu        "bash"     36 seconds ago   Exited (0) 2 seconds ago             angry_borg
a09fc5b98b54   hello-world   "/hello"   3 minutes ago    Exited (0) 3 minutes ago             eager_driscoll

$ docker stats --no-stream
CONTAINER ID   NAME      CPU %     MEM USAGE / LIMIT   MEM %     NET I/O   BLOCK I/O   PIDS
```

## 확인한 항목

- 이미지 다운로드/목록 확인: `docker images` (실행 전 빈 목록 → hello-world 실행 후 이미지 생성 확인)
- 컨테이너 실행/목록 확인: `docker ps`, `docker ps -a`
- 로그 확인: `docker logs`
- 리소스 확인: `docker stats --no-stream` (실행 중인 컨테이너가 없어 빈 결과 — hello-world, ubuntu 모두 Exited 상태였기 때문)
- `hello-world` 실행 성공
- `ubuntu` 컨테이너 진입 후 `ls`, `echo` 명령 수행 성공

## 컨테이너 종료 vs 유지 관찰

- `docker run hello-world`: 컨테이너가 작업(메시지 출력)을 마치면 프로세스가 끝나서 자동으로 종료(Exited) 상태가 됨
- `docker run -it ubuntu bash`: `-it` 옵션으로 대화형 셸에 진입, 내부에서 `exit`을 입력하기 전까지는 컨테이너가 계속 살아있음. `exit`으로 셸 프로세스가 끝나면 컨테이너도 같이 종료됨
- `docker attach <CONTAINER ID>`: 메인 프로세스 화면에 바로 연결하기
- `docker exec -it <CONTAINER ID> /bin/bash`: 컨테이너 내부에 안전하게 새로운 bash 쉘 열기