# GitHub SSH 키 설정

## 목적

HTTPS 대신 SSH 방식으로 GitHub에 인증하여 push가 가능하도록 키를 등록하고 동작을 확인한다.

## 수행 명령 및 결과

### 1. SSH 키 생성

```
$ ssh-keygen -t ed25519 -C "beenjeong02@gmail.com"
Generating public/private ed25519 key pair.
Enter file in which to save the key (/Users/beenjeong022655/.ssh/id_ed25519):
Enter passphrase for "/Users/beenjeong022655/.ssh/id_ed25519" (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in /Users/beenjeong022655/.ssh/id_ed25519
Your public key has been saved in /Users/beenjeong022655/.ssh/id_ed25519.pub
```

### 2. 공개키 확인 (GitHub에 등록할 값)

```
$ cat ~/.ssh/id_ed25519.pub
ssh-ed25519 (공개키 값은 보안상 생략) beenjeong02@gmail.com
```

> 이 값을 GitHub → Settings → SSH and GPG keys → New SSH key(Authentication Key)에 등록

### 3. SSH 연결 테스트

```
$ ssh -T git@github.com
The authenticity of host 'github.com' can't be established.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added 'github.com' to the list of known hosts.
Hi b0e2! You've successfully authenticated, but GitHub does not provide shell access.
```

### 4. 원격 저장소 URL을 SSH로 변경

```
$ git remote set-url origin git@github.com:b0e2/codyssey-e1-1.git

$ git remote -v
origin  git@github.com:b0e2/codyssey-e1-1.git (fetch)
origin  git@github.com:b0e2/codyssey-e1-1.git (push)
```

### 5. SSH 방식으로 push 확인

```
$ git push
Everything up-to-date
```

## 결과 분석

- `ssh -T git@github.com` 실행 결과 "Hi b0e2! You've successfully authenticated"가 출력되어, 등록한 공개키로 GitHub 인증이 정상적으로 이루어짐을 확인했다.
- 원격 저장소 URL을 `https://github.com/...`에서 `git@github.com:...` 형식으로 변경한 뒤 `git push`를 실행한 결과, 별도의 아이디/비밀번호(또는 토큰) 입력 없이 정상적으로 통신되었다.
- HTTPS 방식은 매 인증마다 자격 증명(토큰 등)을 요구하거나 credential helper에 의존하는 반면, SSH 방식은 키 쌍 기반으로 한 번 등록해두면 이후 인증 과정 없이 안전하게 통신할 수 있다는 차이를 확인했다.

## 확인한 항목

- SSH 키 쌍 생성 및 GitHub 계정에 공개키(Authentication Key) 등록
- `ssh -T` 명령으로 인증 성공 확인
- 원격 저장소를 SSH 방식으로 전환 후 push 정상 동작 확인