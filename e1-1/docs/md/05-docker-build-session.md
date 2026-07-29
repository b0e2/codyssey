# Docker 커스텀 이미지 빌드 및 컨테이너 실행

## 선택한 방식

(B) Linux 베이스 이미지(ubuntu:22.04) + 패키지/사용자/환경변수/헬스체크 추가

## Dockerfile

```
FROM ubuntu:22.04

WORKDIR /app

RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

RUN useradd --create-home appuser

COPY main.py .

ENV PORT=8000
ENV APP_ENV=production

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 커스텀 포인트 요약

- 베이스 이미지: `ubuntu:22.04` (순수 Linux 배포판)
- 패키지 설치: `apt-get`으로 `python3`, `python3-pip` 직접 설치
- 사용자 추가: `appuser`라는 비-root 유저 생성 후 `USER appuser`로 전환 (보안 강화)
- 환경변수: `PORT`, `APP_ENV`로 설정값 분리
- 헬스체크: 30초 간격으로 `/health` 엔드포인트 확인

## 빌드 및 실행 명령 / 결과

```
$ docker build -t my-web:1.0 .
[+] Building 1.7s (12/12) FINISHED            docker:orbstack
 => [internal] load build definition from Dockerfile     0.1s
 => [internal] load metadata for docker.io/library/ubun  1.1s
 => [1/7] FROM docker.io/library/ubuntu:22.04             0.0s
 => CACHED [2/7] WORKDIR /app                             0.0s
 => CACHED [3/7] RUN apt-get update && apt-get install    0.0s
 => CACHED [4/7] COPY requirements.txt .                  0.0s
 => CACHED [5/7] RUN pip3 install --no-cache-dir -r req   0.0s
 => CACHED [6/7] RUN useradd --create-home appuser        0.0s
 => CACHED [7/7] COPY main.py .                           0.0s
 => exporting to image                                    0.0s
 => => naming to docker.io/library/my-web:1.0             0.0s

$ docker images
REPOSITORY    TAG       IMAGE ID       CREATED         SIZE
my-web        1.0       b22c99592f20   9 minutes ago   454MB
ubuntu        latest    de7345b16e94   2 weeks ago     100MB
hello-world   latest    e2ac70e7319a   4 months ago    10.1kB

$ docker run -d -p 8080:8000 --name my-web-8080 my-web:1.0
543e358c6a37e5c6d3a162092df5e884be4a23aefa8acab90a066f3611058a67

$ docker run -d -p 8081:8000 --name my-web-8081 my-web:1.0
6dfc7648cc9cd68bfed96ba204699f461643690e0846695bccd2fb891399ed2e

$ docker ps
CONTAINER ID   IMAGE        COMMAND                  CREATED         STATUS                            PORTS                                         NAMES
6dfc7648cc9c   my-web:1.0   "uvicorn main:app --…"   4 seconds ago   Up 4 seconds (health: starting)   0.0.0.0:8081->8000/tcp, [::]:8081->8000/tcp   my-web-8081
543e358c6a37   my-web:1.0   "uvicorn main:app --…"   9 seconds ago   Up 8 seconds (health: starting)   0.0.0.0:8080->8000/tcp, [::]:8080->8000/tcp   my-web-8080

$ curl http://localhost:8080
{"message":"Hello"}

$ curl http://localhost:8080/health
{"status":"ok"}

$ curl http://localhost:8081
{"message":"Hello"}

$ curl http://localhost:8081/health
{"status":"ok"}

$ docker ps
CONTAINER ID   IMAGE        COMMAND                  CREATED          STATUS                             PORTS                                         NAMES
6dfc7648cc9c   my-web:1.0   "uvicorn main:app --…"   30 seconds ago   Up 30 seconds (health: starting)   0.0.0.0:8081->8000/tcp, [::]:8081->8000/tcp   my-web-8081
543e358c6a37   my-web:1.0   "uvicorn main:app --…"   35 seconds ago   Up 34 seconds (healthy)            0.0.0.0:8080->8000/tcp, [::]:8080->8000/tcp   my-web-8080
```

## 포트 매핑 접속 증거

![포트 8080 접속](../assets/port-8080-docs.png)
![포트 8081 접속](../assets/port-8081-health.png)

## 확인한 항목

- 커스텀 이미지 빌드 성공 (`my-web:1.0`)
- 컨테이너 실행 성공, 서로 다른 포트(8080, 8081)로 2회 접속 확인
- 헬스체크 정상 동작 확인 (`health: starting` → `healthy`)