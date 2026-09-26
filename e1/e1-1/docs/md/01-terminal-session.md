# 터미널 기본 조작

작업 디렉토리: `codyssey-e1-1/box`

## 수행 명령 및 결과
```
$ pwd
/Users/beenjeong022655/codyssey-e1-1

$ ls -la
total 16
drwxr-xr-x   6 beenjeong022655  beenjeong022655   192 Jul 28 11:44 .
drwxr-x---+ 21 beenjeong022655  beenjeong022655   672 Jul 28 11:49 ..
drwxr-xr-x  12 beenjeong022655  beenjeong022655   384 Jul 28 11:39 .git
-rw-r--r--   1 beenjeong022655  beenjeong022655   578 Jul 28 11:38 .gitignore
drwxr-xr-x   3 beenjeong022655  beenjeong022655    96 Jul 28 11:45 docs
-rw-r--r--   1 beenjeong022655  beenjeong022655  1221 Jul 28 11:38 README.md

$ mkdir box
$ cd box

$ touch note.txt
$ echo "Hello World" > note.txt
$ cat note.txt
Hello World

$ cp note.txt note_copy.txt
$ mv note_copy.txt note_final.txt

$ ls -la
total 16
drwxr-xr-x  4 beenjeong022655  beenjeong022655  128 Jul 28 11:50 .
drwxr-xr-x  7 beenjeong022655  beenjeong022655  224 Jul 28 11:49 ..
-rw-r--r--  1 beenjeong022655  beenjeong022655   12 Jul 28 11:50 note_final.txt
-rw-r--r--  1 beenjeong022655  beenjeong022655   12 Jul 28 11:49 note.txt

$ rm note_final.txt
$ ls -la
total 8
drwxr-xr-x  3 beenjeong022655  beenjeong022655   96 Jul 28 11:51 .
drwxr-xr-x  7 beenjeong022655  beenjeong022655  224 Jul 28 11:49 ..
-rw-r--r--  1 beenjeong022655  beenjeong022655   12 Jul 28 11:49 note.txt

$ cd ..

```

## 확인한 항목
- 현재 위치 확인: `pwd`
- 목록 확인(숨김 파일 포함): `ls -la` (repo 루트에서 `.git`, `.gitignore` 확인)
- 이동: `cd`
- 생성: `mkdir`, `touch`
- 복사: `cp`
- 이동/이름변경: `mv`
- 삭제: `rm`
- 파일 내용 확인: `cat`