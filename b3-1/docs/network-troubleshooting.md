# Network Troubleshooting

외부에서 웹 서비스에 접속되지 않을 때의 점검 순서입니다.

바깥쪽 경로부터 안쪽으로 좁혀 가며 확인합니다.

```text
DNS → 라우팅 → 보안 그룹 → 네트워크 ACL → 퍼블릭 IP → 호스트 Nginx → 컨테이너
```

## 1. DNS

도메인이 현재 인스턴스를 가리키는지 확인합니다.

```bash
dig +short b0e2-b3.ddns.net
dig +short b0e2-b3.ddns.net @8.8.8.8
```

| 증상 | 원인 | 조치 |
|---|---|---|
| 응답 없음 | 레코드 미등록 | A 레코드 생성 |
| 이전 IP 응답 | 인스턴스 재생성 후 미갱신 | A 레코드를 현재 공인 IP로 변경 |
| 로컬과 외부 응답 불일치 | 캐시 | TTL 경과 대기 |

## 2. 라우팅

퍼블릭 서브넷의 라우팅 테이블에 인터넷 게이트웨이 경로가 있는지 확인합니다.

```bash
aws ec2 describe-route-tables \
  --filters Name=association.subnet-id,Values=<subnet-id> \
  --query 'RouteTables[].Routes'
```

`0.0.0.0/0` 의 대상이 `igw-` 로 시작해야 합니다. 경로가 없으면 인스턴스는 외부와 통신할 수 없습니다.

## 3. 보안 그룹

인바운드 규칙에 필요한 포트가 열려 있는지 확인합니다.

```bash
aws ec2 describe-security-groups \
  --group-ids <sg-id> \
  --query 'SecurityGroups[].IpPermissions'
```

| 확인 항목 | 기대값 |
|---|---|
| 80 | `0.0.0.0/0` |
| 443 | `0.0.0.0/0` |
| 22 | 관리자 IP `/32` |

보안 그룹은 상태 저장 방식이므로 인바운드만 열려 있으면 응답 트래픽은 자동으로 허용됩니다.

## 4. 네트워크 ACL

서브넷 단위 차단 여부를 확인합니다. 네트워크 ACL은 상태 비저장이므로 인바운드와 아웃바운드를 모두 확인해야 합니다.

```bash
aws ec2 describe-network-acls \
  --filters Name=association.subnet-id,Values=<subnet-id> \
  --query 'NetworkAcls[].Entries'
```

## 5. 퍼블릭 IP

인스턴스에 공인 IP가 할당되어 있는지 확인합니다.

```bash
aws ec2 describe-instances \
  --instance-ids <instance-id> \
  --query 'Reservations[].Instances[].[PublicIpAddress,PrivateIpAddress,State.Name]'
```

서브넷의 퍼블릭 IP 자동 할당이 꺼져 있으면 인스턴스 재생성 시 공인 IP가 없습니다.

## 6. 호스트 Nginx

인스턴스 내부에서 서비스가 응답하는지 확인합니다.

```bash
sudo systemctl status nginx
sudo nginx -t
sudo ss -tlnp | grep -E ':80|:443|:8080'
curl -I http://127.0.0.1
```

| 증상 | 원인 | 조치 |
|---|---|---|
| 502 Bad Gateway | 컨테이너 중지 | 컨테이너 상태 확인 |
| 연결 거부 | Nginx 중지 | `systemctl start nginx` |
| 기본 페이지 노출 | 기본 사이트 활성화 | `sites-enabled/default` 제거 |

## 7. 컨테이너

```bash
docker ps
docker inspect --format='{{.State.Health.Status}}' b3-1-web
docker logs --tail 50 b3-1-web
curl -I http://127.0.0.1:8080
```

컨테이너는 `127.0.0.1:8080` 에만 바인딩되어 있으므로 외부에서 직접 접근되지 않는 것이 정상입니다.

## 빠른 점검 명령

```bash
dig +short b0e2-b3.ddns.net
curl -I http://b0e2-b3.ddns.net
curl -I https://b0e2-b3.ddns.net
curl -s https://b0e2-b3.ddns.net/health
```

각 단계의 결과가 기대와 다르면 해당 단계에서 멈추고 원인을 먼저 해결합니다.
