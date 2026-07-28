# 권한 변경 실습

작업 디렉토리: `codyssey-e1-1/perm`

## 수행 명령 및 결과

```

​$ cd perm

$ mkdir perm-dir
$ touch perm-file.sh

$ ls -l perm-dir perm-file.sh
-rw-r--r--  1 beenjeong022655  beenjeong022655  0 Jul 28 12:50 perm-file.sh

perm-dir:
total 0

$ chmod 700 perm-dir
$ chmod 755 perm-file.sh

$ ls -l perm-dir perm-file.sh
-rwxr-xr-x  1 beenjeong022655  beenjeong022655  0 Jul 28 12:50 perm-file.sh

perm-dir:
total 0
​
```

## 확인한 항목
- 파일 1개(`perm-file.sh`), 디렉토리 1개(`perm-dir`)에 대한 권한 변경 전/후 비교
- `perm-file.sh`: `644`(rw-r--r--) → `755`(rwxr-xr-x)
- `perm-dir`: `chmod 700` 적용

## 권한 개념 정리

**r/w/x와 755, 644**
- 7 = rwx(4+2+1), 5 = r-x(4+1), 4 = r--(4)
- 755 → 소유자 rwx, 그룹/기타 r-x
- 644 → 소유자 rw-, 그룹/기타 r--

**파일에서의 r/w/x**
- r — 내용을 읽을 수 있다 (cat, 에디터로 열기)
- w — 내용을 수정할 수 있다
- x — 그 파일을 프로그램으로 실행할 수 있다

**디렉토리에서의 r/w/x**
- r — 디렉토리 안의 파일 목록을 볼 수 있다 (ls)
- w — 디렉토리 안에서 파일을 생성/삭제할 수 있다
- x — 그 디렉토리 안으로 들어갈 수 있다 (cd), 또는 안에 있는 파일에 접근할 수 있다