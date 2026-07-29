# 볼륨 백업 / 복원

볼륨 영속성 실습(06)에서는 "컨테이너를 삭제해도 데이터가 유지됨"을 확인했다. 여기서는 한 단계 더 나아가, **볼륨 자체가 손실되는 상황에 대비한 백업/복원**을 다룬다. 임시 `alpine` 컨테이너에 볼륨과 호스트 디렉토리를 함께 마운트해 `tar` 아카이브로 백업하고, 원본 볼륨을 삭제한 뒤 새 볼륨에 복원한다.

## 1. 백업 대상 준비

```
$ docker volume create backup-demo
backup-demo

$ docker run -d --name bk-src -v backup-demo:/data alpine sleep 300
2b7c1a...

$ docker exec bk-src sh -c 'echo "important data v1" > /data/note.txt; echo "config=prod" > /data/app.conf; ls /data'
app.conf
note.txt
```

## 2. tar 아카이브로 백업

볼륨을 읽기 전용(`:ro`)으로, 호스트 현재 디렉토리를 백업 저장 위치로 마운트해 아카이브를 생성한다.

```
$ docker run --rm -v backup-demo:/data:ro -v "$(pwd)":/backup alpine \
    tar czvf /backup/backup-demo.tar.gz -C /data .
./
./note.txt
./app.conf

$ ls -lh backup-demo.tar.gz
-rw-r--r--  1  ...  182B  backup-demo.tar.gz
```

## 3. 원본 삭제 후 새 볼륨에 복원

원본 볼륨을 완전히 삭제해 데이터가 사라진 상황을 만든 뒤, 백업 아카이브로 새 볼륨에 복원한다.

```
# 원본 볼륨/컨테이너 완전 삭제
$ docker rm -f bk-src
bk-src
$ docker volume rm backup-demo
backup-demo

# 새 볼륨 생성 후 아카이브 복원
$ docker volume create backup-restored
backup-restored
$ docker run --rm -v backup-restored:/data -v "$(pwd)":/backup alpine \
    tar xzvf /backup/backup-demo.tar.gz -C /data
./
./note.txt
./app.conf
```

## 4. 복원 검증

```
$ docker run --rm -v backup-restored:/data alpine cat /data/note.txt /data/app.conf
important data v1
config=prod
```

**확인 결과**: 원본 볼륨(`backup-demo`)을 삭제한 뒤에도 tar 아카이브로 새 볼륨(`backup-restored`)에 데이터를 그대로 복원할 수 있었다. **영속성**(컨테이너 삭제 후 데이터 유지)과 **백업**(볼륨 자체 손실 대비)은 서로 다른 층위의 안전장치이며, 실제 운영에서는 두 가지를 함께 사용한다. 정기 스냅샷이 필요하면 이 `tar` 절차를 크론으로 예약하거나 `rsync`로 원격 저장소에 복제할 수 있다.

## 확인한 항목

- `docker run --rm -v <volume>:/data -v "$(pwd)":/backup alpine tar czvf ...` 로 볼륨을 파일로 백업
- 원본 볼륨 삭제 후, `tar xzvf`로 새 볼륨에 복원하여 데이터 일치 확인
- 백업 아카이브는 호스트 파일이므로 외부 스토리지/원격으로 복제해 재해에 대비 가능

