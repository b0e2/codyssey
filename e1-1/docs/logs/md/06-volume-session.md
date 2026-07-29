# 바인드 마운트 및 볼륨 영속성 검증

## 1. 바인드 마운트 (변경 반영 확인)

호스트 디렉토리를 컨테이너에 직접 연결하여, 호스트에서의 파일 변경이 컨테이너 재시작 없이 즉시 반영되는지 확인한다.

```
$ mkdir -p ~/codyssey-e1-1/bind-test
$ echo "original text" > ~/codyssey-e1-1/bind-test/hello.txt

$ docker run -d --name bind-demo -v ~/codyssey-e1-1/bind-test:/data ubuntu sleep infinity
8a34d9f1117bf9c54562c806c6f8406d97bbdc6fd34a2251d517b0f2a45f3950

$ docker exec bind-demo cat /data/hello.txt
original text

# 호스트에서 파일 수정 (컨테이너 재시작 없이)
$ echo "modify text" >> ~/codyssey-e1-1/bind-test/hello.txt

$ docker exec bind-demo cat /data/hello.txt
original text
modify text
```

**확인 결과**: 호스트에서 파일을 수정하자, 컨테이너를 재시작하지 않고도 `docker exec`으로 확인한 내용에 변경 사항이 즉시 반영되었다. 바인드 마운트는 호스트 파일시스템 경로를 컨테이너에 그대로 연결하는 방식이기 때문이다.

## 2. 볼륨 영속성 검증

Docker가 관리하는 볼륨을 생성하고, 컨테이너를 삭제한 뒤에도 데이터가 유지되는지 확인한다.

```
$ docker volume create mydata
mydata

$ docker run -d --name vol-test -v mydata:/data ubuntu sleep infinity
87fc8840fcad454eb87c1be5d97c424de5a3755a376e2e9f81b8cbf36fa7859a

$ docker exec vol-test bash -c "echo hi > /data/hello.txt && cat /data/hello.txt"
hi

$ docker rm -f vol-test
vol-test

# 컨테이너를 삭제한 후, 같은 볼륨을 새 컨테이너에 연결
$ docker run -d --name vol-test2 -v mydata:/data ubuntu sleep infinity
4cf2acb7c24f11bb33d7745d41342008d9545deb1a063bce51f6b8230cb0deb8

$ docker exec vol-test2 cat /data/hello.txt
hi
```

**확인 결과**: `vol-test` 컨테이너를 완전히 삭제(`docker rm -f`)한 후, 같은 볼륨(`mydata`)을 연결한 새 컨테이너(`vol-test2`)에서 데이터(`hi`)가 그대로 유지됨을 확인했다. 볼륨은 컨테이너 생명주기와 독립적으로 데이터를 보존한다.

## 3. 볼륨 백업 / 복원 (tar 아카이브)

볼륨 영속성과 별개로, 볼륨을 파일로 백업해 두면 볼륨 자체가 삭제돼도 복구할 수 있다. 임시 `alpine` 컨테이너에 볼륨과 호스트 디렉토리를 함께 마운트해 `tar`로 아카이브한다.

```
# 볼륨(mydata)을 읽기전용으로 마운트해 tar 아카이브 생성
$ docker run --rm -v mydata:/data:ro -v "$(pwd)":/backup alpine tar czvf /backup/mydata.tar.gz -C /data .
./
./hello.txt

# 원본 볼륨을 완전히 삭제한 뒤, 새 볼륨에 복원
$ docker volume rm mydata
$ docker volume create mydata-restored
$ docker run --rm -v mydata-restored:/data -v "$(pwd)":/backup alpine tar xzvf /backup/mydata.tar.gz -C /data
./
./hello.txt

# 복원 검증
$ docker run --rm -v mydata-restored:/data alpine cat /data/hello.txt
hi
```

**확인 결과**: 원본 볼륨(`mydata`)을 삭제한 뒤에도 tar 아카이브로 새 볼륨(`mydata-restored`)에 데이터(`hi`)를 복원할 수 있었다. 영속성(컨테이너 삭제 후 유지)과 백업(볼륨 자체 손실 대비)은 서로 다른 층위의 안전장치다.

## 4. 트러블슈팅

**문제**: 실습 후 정리 과정에서 볼륨 삭제 시도 시 에러 발생

```
$ docker volume rm mydata
Error response from daemon: remove mydata: volume is in use - [4cf2acb7c24f11bb33d7745d41342008d9545deb1a063bce51f6b8230cb0deb8]
```

**원인 가설**: `vol-test2` 컨테이너가 아직 `mydata` 볼륨을 사용 중인 상태(실행 중)라서 삭제가 거부됨

**확인**: `docker ps`로 `vol-test2`가 여전히 실행 중인지 확인

**해결**: 볼륨을 사용 중인 컨테이너를 먼저 삭제한 후 볼륨 삭제

```
$ docker rm -f vol-test2
$ docker volume rm mydata
```

## 확인한 항목

- 바인드 마운트 실행 명령 + 호스트 변경 전/후 비교 완료
- Docker 볼륨 생성/연결/검증 명령 + 컨테이너 삭제 전/후 비교 완료
- 볼륨 백업(tar)→원본 삭제→새 볼륨 복원 과정 실행 로그 기록