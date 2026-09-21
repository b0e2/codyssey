# HTTPS Setup

외부 도메인 연결과 HTTPS 적용 절차입니다.

## 사전 조건

- [ ] EC2 인스턴스가 실행 중이고 공인 IP가 할당되어 있다
- [ ] 퍼블릭 서브넷 라우팅 테이블에 `0.0.0.0/0 → IGW` 경로가 있다
- [ ] 보안 그룹에서 80, 443이 열려 있다
- [ ] 호스트 Nginx가 실행 중이고 컨테이너로 프록시된다
- [ ] 사용할 도메인이 준비되어 있다

## 1. 포트 확인

```bash
aws ec2 describe-security-groups --group-ids <sg-id> \
  --query 'SecurityGroups[].IpPermissions[].[FromPort,ToPort,IpRanges[].CidrIp]'
```

80과 443이 `0.0.0.0/0` 으로 열려 있어야 인증서 발급에 필요한 HTTP-01 검증이 통과합니다.

## 2. 호스트 방화벽 확인

Ubuntu 기본 이미지에서는 UFW가 비활성 상태입니다. 활성화되어 있다면 다음을 허용합니다.

```bash
sudo ufw status
sudo ufw allow 'Nginx Full'
```

## 3. DNS 연결

No-IP에서 호스트를 생성하고 A 레코드를 인스턴스 공인 IP로 지정합니다.

```bash
dig +short b0e2-b3.ddns.net
curl -s http://169.254.169.254/latest/meta-data/public-ipv4
```

두 값이 같아야 합니다. 인스턴스를 재생성하면 공인 IP가 바뀌므로 레코드를 다시 수정해야 합니다.

![DNS A 레코드](screenshots/dns-a-record.png)

## 4. HTTP 응답 확인

```bash
curl -I http://b0e2-b3.ddns.net
```

인증서 발급 전에는 200이 반환되어야 합니다. 여기서 실패하면 DNS나 보안 그룹부터 확인합니다.

## 5. 인증서 발급

```bash
sudo apt-get install -y certbot python3-certbot-nginx

sudo certbot --nginx \
  -d b0e2-b3.ddns.net \
  --non-interactive \
  --agree-tos \
  --email <이메일> \
  --redirect
```

`--redirect` 옵션을 사용하면 HTTP 요청을 HTTPS로 보내는 설정이 함께 생성됩니다.

![Let's Encrypt 인증서](screenshots/certbot-certificate.png)

## 6. 결과 확인

```bash
curl -i https://b0e2-b3.ddns.net/health
curl -I http://b0e2-b3.ddns.net
```

![HTTPS 검증](screenshots/curl-https-verification.png)

## 7. 자동 갱신 점검

```bash
sudo certbot renew --dry-run
systemctl list-timers | grep certbot
```

Certbot 설치 시 갱신 타이머가 등록됩니다. 시뮬레이션이 성공하면 만료 전 자동 갱신됩니다.

## 자주 발생하는 문제

| 증상 | 원인 | 조치 |
|---|---|---|
| `Timeout during connect` | 80 포트 차단 | 보안 그룹과 라우팅 확인 |
| `DNS problem: NXDOMAIN` | 레코드 없음 | A 레코드 생성 후 재시도 |
| 검증은 통과했으나 접속 불가 | 443 미개방 | 보안 그룹에 443 추가 |
| 인증서 발급 반복 실패 | 발급 제한 | 스테이징 환경으로 먼저 시험 |

발급 시험이 필요하면 `--dry-run` 또는 스테이징 서버를 사용해 실제 발급 제한을 소모하지 않도록 합니다.
