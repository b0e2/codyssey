# 미션: 내 컴퓨터에 개발자용 '작업실' 꾸미기

터미널, Docker, Git 환경을 직접 세팅하여 재현 가능한 개발 워크스테이션을 구축한다.

---

## 1) 프로젝트 개요

코드가 "내 컴퓨터에서만" 돌아가는 문제를 줄이고, 누구나 같은 방식으로 실행·배포·디버깅할 수 있는 환경을 구성하는 것이 목표다.

- 터미널(CLI)로 작업 디렉토리와 파일 권한을 정리
- Docker를 설치·점검하고 컨테이너를 실행/관리
- FastAPI 웹 서버를 직접 작성한 Dockerfile로 컨테이너화
- 포트 매핑으로 외부 접속을 확인하고, 바인드 마운트/볼륨으로 "변경 반영"과 "데이터 영속성"을 검증
- Git/GitHub로 전체 과정을 버전 관리

---

## 2) 실행 환경

| 항목 | 값 |
|---|---|
| OS | macOS |
| Shell | zsh (로그 녹화 시 bash 사용) |
| 터미널 | VSCode 통합 터미널 / macOS 기본 터미널 |
| Docker | 28.5.2 (OrbStack 기반) |
| Docker Compose | v2.40.3 |
| Git | 2.x |
| Python | 3.12.13 (로컬), 3.10 (컨테이너 내부, ubuntu:22.04 기본) |

Docker 설치 및 데몬 동작 확인 결과 (발췌):

```
$ docker --version
Docker version 28.5.2, build ecc6942

$ docker info
Client:
 Version:    28.5.2
 Context:    orbstack
...
Server:
 Server Version: 28.5.2
 Storage Driver: overlay2
 Operating System: OrbStack
 OSType: linux
 CPUs: 6
 Total Memory: 15.67GiB
```

전체 출력 → [03-docker-basic-session.md](docs/logs/md/03-docker-basic-session.md)

> 서울캠퍼스 환경의 sudo 권한 제약으로 인해, Docker Desktop 대신 **OrbStack**을 사용해 Docker 엔진을 구동했다.

---

## 3) 수행 체크리스트

### 필수 과제

- [x] 터미널 기본 조작 및 폴더 구성
- [x] 권한 변경 실습 (파일 1, 디렉토리 1)
- [x] Docker 설치/점검
- [x] Docker 기본 운영 명령 (images / ps / logs / stats)
- [x] hello-world 실행
- [x] ubuntu 컨테이너 진입 및 attach/exec 차이 관찰
- [x] Dockerfile 작성 및 커스텀 이미지 빌드 (B안: Linux 베이스 + 패키지/사용자/환경변수/헬스체크)
- [x] 포트 매핑 접속 (2회)
- [x] 포트 충돌 진단 (lsof → 프로세스 확인 → 포트 변경)
- [x] 바인드 마운트 반영 확인
- [x] 볼륨 영속성 검증
- [x] 볼륨 백업/복원 (tar 아카이브)
- [x] Git 설정 + GitHub/VSCode 연동
- [x] GitHub push 로그 기록
- [x] 트러블슈팅 2건 이상

### 보너스 과제

- [x] Docker Compose 단일 서비스
- [x] Compose 멀티 컨테이너 (web + redis)
- [x] 컨테이너 간 네트워크 통신 확인
- [x] Compose 운영 명령 (up/down/ps/logs)
- [x] 환경 변수 활용
- [x] GitHub SSH 키 설정

---

## 4) 검증 방법 및 결과 위치

| # | 수행 항목 | 검증 방법 (사용 명령) | 결과 |
|---|---|---|---|
| 01 | 터미널 기본 조작 | `pwd`, `ls -la`, `mkdir`, `cd`, `touch`, `cat`, `cp`, `mv`, `rm` | [01-terminal-session.md](docs/logs/md/01-terminal-session.md) |
| 02 | 권한 변경 실습 | `chmod 700` / `chmod 755` 전/후 `ls -l` 비교, `cp`/`mv`/`rm`로 실습 파일 정리 | [02-terminal-permissions.md](docs/logs/md/02-terminal-permissions.md) |
| 03 | Docker 설치/점검 | `docker --version`, `docker info` | [03-docker-basic-session.md](docs/logs/md/03-docker-basic-session.md) |
| 04 | Docker 기본 운영 + 컨테이너 실행 | `docker images`, `docker ps -a`, `docker logs`, `docker stats`, `docker run hello-world`, `docker run -it ubuntu bash` | [04-docker-run-session.md](docs/logs/md/04-docker-run-session.md) |
| — | attach vs exec 차이 관찰 | `docker exec` 후 `exit` → 유지 / `docker attach` 후 `Ctrl+C` → 종료, `docker ps`로 전후 비교 | [attach-exec-session.md](docs/logs/md/attach-exec-session.md) |
| 05 | 커스텀 이미지 빌드 + 포트 매핑 | `docker build`, `docker run -d -p 8080:8000` / `-p 8081:8000`, `curl`, 브라우저 접속 | [05-docker-build-session.md](docs/logs/md/05-docker-build-session.md) |
| 05-1 | 포트 충돌 진단 | `lsof -nP -i :8080`으로 점유 프로세스 확인 후 호스트 포트를 8082로 변경 재실행 | [05-1-port-conflict-session.md](docs/logs/md/05-1-port-conflict-session.md) |
| 06 | 바인드 마운트 + 볼륨 영속성 + 백업/복원 | 호스트 파일 수정 반영 확인 / 컨테이너 삭제 후 데이터 유지 / `tar`로 볼륨 백업→삭제→복원 검증 | [06-volume-session.md](docs/logs/md/06-volume-session.md) |
| 07 | Git 설정 + GitHub 연동 + Push | `git config --list`, VSCode 연동, `git push origin main` 원격 반영 출력 | [07-git-setup-session.md](docs/logs/md/07-git-setup-session.md) |

### 증거 자료 (스크린샷)

| 항목 | 파일 |
|---|---|
| 포트 매핑 접속 (8080) | [port-8080-docs.png](docs/logs/assets/port-8080-docs.png) |
| 포트 매핑 접속 (8081) | [port-8081-health.png](docs/logs/assets/port-8081-health.png) |
| VSCode GitHub 연동 | [vscode-github.png](docs/logs/assets/vscode-github.png) |

---

## 5) 커스텀 이미지 (B안)

**선택한 베이스**: `ubuntu:22.04` (순수 Linux 배포판)

| 커스텀 포인트 | 목적 |
|---|---|
| `apt-get install python3 python3-pip` | 베이스 이미지에 없는 Python 런타임을 직접 설치 |
| `RUN useradd --create-home appuser` + `USER appuser` | 컨테이너를 root가 아닌 전용 유저로 실행하여 권한 최소화 |
| `ENV PORT`, `ENV APP_ENV` | 설정값을 코드에서 분리하여 실행 환경별로 주입 가능하게 함 |
| `HEALTHCHECK` (30초 간격 `/health` 확인) | Docker가 앱 생존 여부를 자동 감시, `docker ps`에서 `(healthy)` 확인 |
| `CMD uvicorn --host 0.0.0.0` | 컨테이너 외부에서 접근 가능하도록 바인딩 (`127.0.0.1`이면 포트 매핑해도 접속 불가) |

빌드/실행 명령 및 결과 → [05-docker-build-session.md](docs/logs/md/05-docker-build-session.md)

**소스 코드**
- 웹 서버: [app/main.py](app/main.py)
- 의존성: [app/requirements.txt](app/requirements.txt)
- Dockerfile: [app/Dockerfile](app/Dockerfile)

---

## 6) 개념 정리 (왜 이런 설계인가)

실습 결과를 넘어, 이 미션의 구조적 원칙을 스스로 설명할 수 있도록 핵심 개념을 정리한다.

### 이미지 vs 컨테이너 — 불변성

- **이미지**: 빌드 시점에 고정된 읽기 전용 템플릿(레이어 스택)이다. 같은 이미지는 몇 번을 실행해도 동일하다 → 불변(immutable).
- **컨테이너**: 이미지를 실행한 인스턴스다. 이미지 레이어 위에 얇은 '쓰기 가능 레이어'를 얹어 동작한다. 컨테이너 안에서 파일을 바꿔도 원본 이미지는 그대로다.
- **사례**: 실행 중인 컨테이너에서 `apt-get install ...`을 해도, 같은 이미지로 새 컨테이너를 띄우면 그 패키지는 없다(변경은 그 컨테이너의 쓰기 레이어에만 존재). 변경을 영구화하려면 `docker commit` 또는 Dockerfile로 새 이미지를 빌드한다.

```
# 컨테이너 안에서만 파일을 추가해도 이미지에는 반영되지 않는다
$ docker run -d --name c1 ubuntu:22.04 sleep 300
$ docker exec c1 bash -c "touch /tmp/only-in-c1 && ls /tmp"
only-in-c1
$ docker run --rm ubuntu:22.04 ls /tmp   # 같은 이미지로 띄운 새 컨테이너
                                          # → /tmp/only-in-c1 없음 (이미지는 불변)
```

→ 그래서 유지해야 할 데이터는 컨테이너가 아니라 **볼륨**에 둔다. (참고: [06-volume-session.md](docs/logs/md/06-volume-session.md))

### 네트워크 네임스페이스와 포트 노출

- 각 컨테이너는 독립된 **네트워크 네임스페이스**를 가진다(자체 IP·포트 공간·인터페이스). 그래서 컨테이너 내부의 8000 포트는 호스트의 8000과 별개다.
- 포트 매핑 `-p 8080:8000`은 호스트 네임스페이스의 8080을 컨테이너의 8000에 잇는 '다리' 역할을 한다. 이 매핑이 없으면 호스트에서 컨테이너 내부 포트에 접근할 수 없다.
- **보안**: `-p 8080:8000`은 기본적으로 `0.0.0.0`(모든 인터페이스)에 바인딩되어 같은 LAN의 다른 기기도 접근할 수 있다. 로컬 개발이나 민감한 서비스는 `-p 127.0.0.1:8080:8000`처럼 루프백에만 노출하는 것이 안전하다.
- 한편 앱의 `uvicorn --host 0.0.0.0`은 '컨테이너 네임스페이스 안에서' 모든 인터페이스 수신을 뜻할 뿐이며, 실제 외부 노출 범위는 호스트의 `-p` 바인딩이 결정한다.

### 절대 경로 vs 상대 경로 — 선택 기준

- **절대 경로**(`~/codyssey-e1-1/bind-test`): 위치가 명확해 어디서 실행하든 같은 대상을 가리킨다(명시성). 바인드 마운트처럼 '호스트의 특정 위치'를 못박아야 할 때 쓴다. 단점은 머신마다 홈 경로가 달라 이식성이 낮다는 것이다.
- **상대 경로**(`./app`, `site/`): 현재 작업 디렉토리(cwd) 기준이라, 저장소를 클론한 누구나 동일하게 동작한다(이식성). 단점은 실행 위치에 의존한다는 것이다.
- **지침**: Dockerfile의 `COPY`나 컨테이너 내부 경로는 상대 경로(이식성)를, 호스트 바인드 마운트 소스는 `$(pwd)`/`~` 확장 또는 절대 경로(명시성)를 권장한다.

### 파일 권한 표기 (755 / 644)

- 권한은 소유자(user) / 그룹(group) / 기타(other) 3자리로 표현하며, 각 자리는 `r=4`, `w=2`, `x=1`의 합이다.
- `755` → 소유자 `rwx`(7), 그룹 `r-x`(5), 기타 `r-x`(5). 실행 파일/디렉토리에 흔히 쓴다.
- `644` → 소유자 `rw-`(6), 그룹 `r--`(4), 기타 `r--`(4). 일반 문서/설정 파일에 쓴다.
- 실습 로그 → [02-terminal-permissions.md](docs/logs/md/02-terminal-permissions.md)

---

## 7) 보너스 과제

| # | 항목 | 검증 방법 | 결과 |
|---|---|---|---|
| 08 | Compose 단일 서비스 | `docker-compose.yml` 작성 후 `docker compose up -d --build` | [08-compose-single-clean-session.md](docs/logs/md/08-compose-single-clean-session.md) |
| 09 | Compose 멀티 컨테이너 (web + redis) | 두 서비스 동시 기동 후 `curl`로 `visit_count` 증가 확인 | [09-compose-multi-session.md](docs/logs/md/09-compose-multi-session.md) |
| 09 | 컨테이너 간 네트워크 통신 | `REDIS_HOST=redis` 서비스명으로 접근, 카운터 값 1→2→3 증가로 통신 증명 | [09-compose-multi-session.md](docs/logs/md/09-compose-multi-session.md) |
| 09 | 환경 변수 활용 | Compose에서 `APP_ENV`, `REDIS_HOST` 주입 → 코드에서 `os.environ.get()`으로 수신 | [09-compose-multi-session.md](docs/logs/md/09-compose-multi-session.md) |
| 10 | Compose 운영 명령 | `up`, `ps`, `logs`, `down` 전체 루틴 수행 | [10-compose-ops-session.md](docs/logs/md/10-compose-ops-session.md) |
| 11 | GitHub SSH 키 설정 | 키 생성 → 공개키 등록 → `ssh -T git@github.com` 인증 확인 → SSH로 push | [11-ssh-key.md](docs/logs/md/11-ssh-key.md) |

**Compose 설정 파일**: [app/docker-compose.yml](app/docker-compose.yml)

---

## 8) 트러블슈팅

수행 과정에서 실제로 겪은 문제와 해결 과정을 정리했다.

| # | 문제 | 원인 | 상세 |
|---|---|---|---|
| 1 | `docker volume rm` 실행 시 `volume is in use` 에러 | 해당 볼륨을 사용 중인 컨테이너가 아직 실행 중이었음 | [troubleshooting.md](docs/logs/md/troubleshooting.md) |
| 2 | `script` 로그 녹화 시 이스케이프 코드로 로그가 깨짐 | zsh 테마(powerlevel10k)가 출력하는 색상/커서 제어 문자가 함께 녹화됨 | [troubleshooting.md](docs/logs/md/troubleshooting.md) |
| 3 | Compose 기동 시 컨테이너가 계속 재시작됨 | `redis.Redis()` 파라미터명 오타 (`decode_response` → `decode_responses`) | [09-compose-multi-session.md](docs/logs/md/09-compose-multi-session.md) |
| 4 | `docker run -p` 실행 시 `port is already allocated` 에러 | 호스트 8080 포트를 이미 다른 컨테이너가 점유 중이었음 | [05-1-port-conflict-session.md](docs/logs/md/05-1-port-conflict-session.md) |

전체 트러블슈팅 문서 → [troubleshooting.md](docs/logs/md/troubleshooting.md)

---

## 9) 디렉토리 구조

```
codyssey-e1-1/
├── README.md
├── .gitignore
├── app/                      # 웹 서버 소스 및 컨테이너 설정
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
├── box/                      # 터미널 기본 조작 실습 디렉토리
├── perm/                     # 권한 변경 실습 디렉토리
├── bind-test/                # 바인드 마운트 실습 디렉토리
└── docs/logs/
    ├── md/                   # 정리된 수행 로그 (마크다운)
    ├── raw/                  # script 명령으로 녹화한 원본 세션 로그
    └── assets/               # 스크린샷 증거 자료
```

> 디렉토리는 **소스 코드(`app/`)** 와 **실습 증거(`docs/logs/`)** 를 명확히 분리해, 평가자가 재현 코드와 수행 로그를 각각 독립적으로 확인할 수 있도록 구성했다.

---

## 10) 재현 방법

```bash
# 저장소 클론
git clone https://github.com/b0e2/codyssey-e1-1.git
cd codyssey-e1-1/app

# Compose로 전체 스택 실행 (web + redis)
docker compose up -d --build

# 동작 확인
curl http://localhost:8080/health     # {"status":"ok"}
curl http://localhost:8080            # {"message":"Hello","visit_count":N}

# 종료
docker compose down
```

> OrbStack(또는 Docker Desktop)이 실행 중이어야 한다.
