# Git 설정 및 GitHub 연동

## 수행 명령 및 결과

```
$ git config --list
credential.helper=osxkeychain
user.name=b0e2
user.email=beenjeong02@gmail.com
core.repositoryformatversion=0
core.filemode=true
core.bare=false
core.logallrefupdates=true
core.ignorecase=true
core.precomposeunicode=true
remote.origin.url=https://github.com/b0e2/codyssey-e1-1.git
remote.origin.fetch=+refs/heads/*:refs/remotes/origin/*
branch.main.remote=origin
branch.main.merge=refs/heads/main
branch.main.vscode-merge-base=origin/main
```

## 확인한 항목

- Git 사용자 정보 설정 완료: `user.name=b0e2`, `user.email=beenjeong02@gmail.com`
- 기본 브랜치 설정 확인: `branch.main.remote=origin`, `branch.main.merge=refs/heads/main`
- 원격 저장소(GitHub) 연동 확인: `remote.origin.url=https://github.com/b0e2/codyssey-e1-1.git`
- VSCode에서 GitHub 로그인 및 저장소 연동 완료 (스크린샷 첨부)

![VSCode GitHub 연동](../assets/vscode-github.png)