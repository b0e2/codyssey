# Docker Compose 단일 서비스

## 목적

지금까지 docker run -d -p 8080:8000 --name my-web-8080 my-web:1.0 같은 긴 실행 명령을 매번 손으로 입력했다. Compose는 이 실행 설정을 docker-compose.yml 파일로 문서화하여, docker compose up 한 줄로 동일한 환경을 재현할 수 있게 한다.

## docker-compose.yml

services:
  web:
    build: .
    ports:
      - "8080:8000"
    environment:
      - APP_ENV=production

## 앱 코드 (main.py, 당시 버전)

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

## 수행 명령 및 결과

$ docker compose down
✔ Container app-web-1  Removed
✔ Network app_default  Removed

$ docker compose up -d --build
[+] Building 1.5s (14/14) FINISHED
 => [1/7] FROM docker.io/library/ubuntu:22.04
 => CACHED [2/7] WORKDIR /app
 => CACHED [3/7] RUN apt-get update && apt-get install -y python3 python3-pip
 => CACHED [4/7] COPY requirements.txt .
 => CACHED [5/7] RUN pip3 install --no-cache-dir -r requirements.txt
 => CACHED [6/7] RUN useradd --create-home appuser
 => CACHED [7/7] COPY main.py .
 => => naming to docker.io/library/app-web
[+] Running 3/3
 ✔ app-web              Built
 ✔ Network app_default  Created
 ✔ Container app-web-1  Started

$ docker compose ps
NAME        IMAGE     COMMAND                  SERVICE   CREATED        STATUS                                     PORTS
app-web-1   app-web   "uvicorn main:app --…"   web       1 second ago   Up Less than a second (health: starting)   0.0.0.0:8080->8000/tcp

$ curl http://localhost:8080/health
{"status":"ok"}

$ curl http://localhost:8080
Internal Server Error

## 결과 분석

- docker compose down → up -d --build로 서비스를 완전히 재생성하는 과정이 명령 한 줄로 재현되었다.
- /health는 Redis와 무관한 엔드포인트라 정상 응답({"status":"ok"})했다.
- /는 main.py에서 Redis 서버(redis_host)에 연결을 시도하는데, 아직 docker-compose.yml에 Redis 서비스를 추가하지 않은 상태라 연결에 실패하여 Internal Server Error가 발생했다. 이는 다음 단계(Compose 멀티 컨테이너)에서 redis 서비스를 추가하면서 해결되었다.

## 확인한 항목

- docker-compose.yml 작성 및 단일 서비스(web) 실행 성공
- docker compose up -d --build로 빌드와 실행이 하나의 명령으로 처리됨을 확인
- docker compose ps로 서비스 상태(healthy) 확인