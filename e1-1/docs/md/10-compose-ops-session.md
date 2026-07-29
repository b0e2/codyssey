# Compose 운영 명령어 (up / down / ps / logs)

## 목적

up, down, ps, logs를 사용해 Compose 환경의 실행/종료/상태/로그를 관리하는 운영 루틴을 익힌다.

## 수행 명령 및 결과

### 로그 확인 (logs)

```
$ docker compose logs web
web-1  | INFO:     Started server process [1]
web-1  | INFO:     Waiting for application startup.
web-1  | INFO:     Application startup complete.
web-1  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
web-1  | INFO:     192.168.97.1:42778 - "GET / HTTP/1.1" 200 OK
web-1  | INFO:     192.168.97.1:42782 - "GET / HTTP/1.1" 200 OK
web-1  | INFO:     192.168.97.1:42790 - "GET / HTTP/1.1" 200 OK
web-1  | INFO:     127.0.0.1:34244 - "GET /health HTTP/1.1" 200 OK

$ docker compose logs redis
redis-1  | 1:C 28 Jul 2026 09:36:53.132 * oO0OoO0OoO0Oo Redis is starting oO0OoO0OoO0Oo
redis-1  | 1:C 28 Jul 2026 09:36:53.132 * Redis version=7.4.10, bits=64, commit=00000000, modified=0, pid=1, just started
redis-1  | 1:M 28 Jul 2026 09:36:53.136 * Running mode=standalone, port=6379.
redis-1  | 1:M 28 Jul 2026 09:36:53.137 * Ready to accept connections tcp
```

### 종료 (down)

```
$ curl http://localhost:8080
{"message":"Hello","visit_count":4}

$ docker compose down
[+] Running 3/3
 ✔ Container app-web-1    Removed
 ✔ Container app-redis-1  Removed
 ✔ Network app_default    Removed

$ docker compose ps
NAME      IMAGE     COMMAND   SERVICE   CREATED   STATUS    PORTS
```

## 결과 분석

- `docker compose logs <서비스명>`으로 web과 redis 각각의 로그를 독립적으로 확인할 수 있었다. 멀티 컨테이너 환경에서 특정 서비스만 골라 로그를 볼 수 있어, 문제가 생겼을 때 어느 컨테이너의 이슈인지 빠르게 구분할 수 있다.
- `docker compose down` 한 번으로 web/redis 컨테이너와 Compose가 생성한 네트워크(`app_default`)까지 한꺼번에 정리되었다. `docker rm`을 컨테이너마다 개별 실행할 필요 없이, 종료 절차 역시 하나의 명령으로 재현 가능함을 확인했다.
- down 이후 `docker compose ps` 결과가 빈 목록으로 나와, 관련 리소스가 완전히 정리되었음을 확인했다.

## 확인한 항목

- `docker compose logs`로 서비스별 로그 확인
- `docker compose down`으로 전체 리소스 정리
- `up` → `ps` → `logs` → `down` 전체 운영 루틴 완료