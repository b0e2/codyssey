# Docker Compose 멀티 컨테이너 (web + redis)

## 목적

웹 서버(web)와 보조 서비스(redis) 두 개 이상을 Compose로 함께 실행하고, 컨테이너 간 네트워크 통신이 가능한지 확인한다.

## docker-compose.yml

```
services:
  web:
    build: .
    ports:
      - "8080:8000"
    environment:
      - APP_ENV=production
      - REDIS_HOST=redis
    depends_on:
      - redis

  redis:
    image: "redis:7-alpine"
```

## 앱 코드 (main.py 발췌)

```
import os
import redis
from fastapi import FastAPI

app = FastAPI()

redis_host = os.environ.get("REDIS_HOST", "localhost")
r = redis.Redis(host=redis_host, port=6379, decode_responses=True)

@app.get("/")
def read_root():
    count = r.incr("visit_count")
    return {"message": "Hello", "visit_count": count}

@app.get("/health")
def read_health():
    return {"status": "ok"}
```

## 수행 명령 및 결과

```
$ docker compose down
✔ Container app-web-1  Removed
✔ Network app_default  Removed

$ docker compose up -d --build
[+] Running 8/8
 ✔ redis Pulled
 ✔ app-web Built
 ✔ Network app_default    Created
 ✔ Container app-redis-1  Started
 ✔ Container app-web-1    Started

$ docker compose ps
NAME          IMAGE            COMMAND                  SERVICE   STATUS                                     PORTS
app-redis-1   redis:7-alpine   "docker-entrypoint.s…"   redis     Up Less than a second                      6379/tcp
app-web-1     app-web          "uvicorn main:app --…"   web       Up Less than a second (health: starting)   0.0.0.0:8080->8000/tcp

$ curl http://localhost:8080
{"message":"Hello","visit_count":1}

$ curl http://localhost:8080
{"message":"Hello","visit_count":2}

$ curl http://localhost:8080
{"message":"Hello","visit_count":3}
```

## 트러블슈팅

**문제**: 최초 `main.py` 작성 시 컨테이너가 계속 재시작되며 정상 기동되지 않음

```
web-1  | TypeError: Redis.__init__() got an unexpected keyword argument 'decode_response'
```

**원인 가설**: `redis.Redis()` 호출 시 파라미터명을 `decode_response`로 잘못 입력(정확한 이름은 `decode_responses`)

**확인**: `docker compose logs web`으로 스택 트레이스를 확인해 오타 지점을 특정

**해결**: `decode_response` → `decode_responses`로 수정 후 `docker compose up -d --build`로 재빌드하여 정상 기동 확인

## 결과 분석

- `REDIS_HOST=redis` 환경변수를 통해 web 서비스가 Redis의 IP 주소를 몰라도 서비스 이름(`redis`)만으로 통신할 수 있음을 확인했다. Compose는 같은 네트워크(`app_default`) 안의 서비스들을 서비스명으로 자동 해석해준다(서비스 디스커버리).
- `/` 엔드포인트를 3회 호출한 결과 `visit_count`가 1 → 2 → 3으로 증가했다. 이는 web 컨테이너가 매 요청마다 redis 컨테이너에 실제로 접속해 카운터 값을 저장·조회하고 있다는 직접적인 증거다.

## 확인한 항목

- web + redis 2개 서비스를 Compose로 함께 실행
- 컨테이너 간 네트워크 통신 성공 확인 (`visit_count` 증가)
- 환경 변수(`REDIS_HOST`)를 통한 서비스 디스커버리 확인