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

Docker 설치 및 데몬 동작 확인 결과 → [03-docker-basic-session.md](docs/logs/md/03-docker-basic-session.md)

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
- [x] 바인드 마운트 반영 확인
- [x] 볼륨 영속성 검증
- [x] Git 설정 + GitHub/VSCode 연동
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

### 필수 과제

| # | 수행 항목 | 검증 방법 (사용 명령) | 결과 |
|---|---|---|---|
| 01 | 터미널 기본 조작 | `pwd`, `ls -la`, `mkdir`, `cd`, `touch`, `cat`, `cp`, `mv`, `rm` | [01-terminal-session.md](docs/logs/md/01-terminal-session.md) |
| 02 | 권한 변경 실습 | `chmod 700` / `chmod 755` 적용 후 `ls -l` 전/후 비교 | [02-terminal-permissions.md](docs/logs/md/02-terminal-permissions.md) |
| 03 | Docker 설치/점검 | `docker --version`, `docker info` | [03-docker-basic-session.md](docs/logs/md/03-docker-basic-session.md) |
| 04 | Docker 기본 운영 + 컨테이너 실행 | `docker images`, `docker ps -a`, `docker logs`, `docker stats`, `docker run hello-world`, `docker run -it ubuntu bash` | [04-docker-run-session.md](docs/logs/md/04-docker-run-session.md) |
| — | attach vs exec 차이 관찰 | `docker exec` 후 `exit` → 유지 / `docker attach` 후 `Ctrl+C` → 종료, `docker ps`로 전후 비교 | [attach-exec-session.md](docs/logs/md/attach-exec-session.md) |
| 05 | 커스텀 이미지 빌드 + 포트 매핑 | `docker build`, `docker run -d -p 8080:8000` / `-p 8081:8000`, `curl`, 브라우저 접속 | [05-docker-build-session.md](docs/logs/md/05-docker-build-session.md) |
| 06 | 바인드 마운트 + 볼륨 영속성 | 호스트 파일 수정 후 `docker exec cat`으로 반영 확인 / 컨테이너 삭제 후 새 컨테이너에서 데이터 유지 확인 | [06-volume-session.md](docs/logs/md/06-volume-session.md) |
| 07 | Git 설정 + GitHub 연동 | `git config --list`, VSCode GitHub 로그인 화면 | [07-git-setup-session.md](docs/logs/md/07-git-setup-session.md) |

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

## 6) 보너스 과제

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

## 7) 트러블슈팅

수행 과정에서 실제로 겪은 문제와 해결 과정을 정리했다.

| # | 문제 | 원인 | 상세 |
|---|---|---|---|
| 1 | `docker volume rm` 실행 시 `volume is in use` 에러 | 해당 볼륨을 사용 중인 컨테이너가 아직 실행 중이었음 | [troubleshooting.md](docs/logs/md/troubleshooting.md) |
| 2 | `script` 로그 녹화 시 이스케이프 코드로 로그가 깨짐 | zsh 테마(powerlevel10k)가 출력하는 색상/커서 제어 문자가 함께 녹화됨 | [troubleshooting.md](docs/logs/md/troubleshooting.md) |
| 3 | Compose 기동 시 컨테이너가 계속 재시작됨 | `redis.Redis()` 파라미터명 오타 (`decode_response` → `decode_responses`) | [09-compose-multi-session.md](docs/logs/md/09-compose-multi-session.md) |

전체 트러블슈팅 문서 → [troubleshooting.md](docs/logs/md/troubleshooting.md)

---

## 8) 디렉토리 구조

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

---

## 9) 재현 방법

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