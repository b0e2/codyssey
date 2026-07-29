# GitHub Push 로그

Git 설정 및 GitHub 연동(07)에 이어, 로컬 커밋을 GitHub 원격 저장소로 실제로 **push**하고 반영 결과를 확인한 로그다. Git(로컬 버전관리)과 GitHub(원격 협업 플랫폼)의 역할 차이를 실제 반영 흐름으로 검증한다.

## 1. 원격 저장소 연결 확인

```
$ git remote -v
origin	https://github.com/b0e2/codyssey-e1-1.git (fetch)
origin	https://github.com/b0e2/codyssey-e1-1.git (push)
```

## 2. 변경 사항 커밋

```
$ git add README.md docs/logs/md/05-1-port-conflict-session.md \
        docs/logs/md/06-1-volume-backup-session.md docs/logs/md/07-1-git-push-session.md
$ git commit -m "docs: 개념 정리 및 포트충돌/볼륨백업/푸시 로그 추가"
[main 5591601] docs: 개념 정리 및 포트충돌/볼륨백업/푸시 로그 추가
```

## 3. GitHub로 push (실제 출력)

로컬 커밋을 GitHub 원격(`origin/main`)으로 push한 실제 출력이다.

```
$ git push origin main
오브젝트 나열하는 중: 16, 완료.
오브젝트 개수 세는 중: 100% (16/16), 완료.
Delta compression using up to 8 threads
오브젝트 압축하는 중: 100% (9/9), 완료.
오브젝트 쓰는 중: 100% (10/10), 7.23 KiB | 7.23 MiB/s, 완료.
Total 10 (delta 3), reused 0 (delta 0), pack-reused 0 (from 0)
remote: Resolving deltas: 100% (3/3), completed with 3 local objects.
To https://github.com/b0e2/codyssey-e1-1.git
   eae7213..5591601  main -> main
```

## 4. 반영 확인

push 직후 GitHub 저장소의 커밋 히스토리에 동일한 커밋이 최신으로 올라온 것을 확인했다. 로컬(Git)에서 관리하던 커밋이 원격(GitHub)에 반영되어, 저장소 링크만으로 누구나 동일한 산출물을 확인할 수 있게 된다.

## 확인한 항목

- `git remote -v`로 원격 저장소(`origin`) 연결 확인
- `git add` → `git commit` → `git push`로 로컬 커밋을 원격에 반영
- push 출력의 `To https://github.com/b0e2/codyssey-e1-1.git` 및 ref 갱신으로 원격 반영 검증
- Git = 로컬 버전관리 / GitHub = 원격 협업 플랫폼의 역할 차이를 실제 흐름으로 확인

> 개인 인증 정보(토큰/비밀번호)는 출력에 포함되지 않도록 확인했다. HTTPS 방식은 macOS 키체인(`credential.helper=osxkeychain`)에 저장된 자격 증명을 사용한다. (SSH 방식은 [11-ssh-key.md](11-ssh-key.md) 참고)
