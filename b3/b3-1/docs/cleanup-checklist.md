# Cleanup Checklist

평가와 증빙 확인이 모두 끝난 뒤에 진행합니다.

2026-09-21 기준으로 아래 항목을 모두 수행해 리소스를 정리했습니다.

삭제 절차를 실제로 수행한 기록은 [Cleanup Evidence](cleanup-evidence.md) 에 있습니다.

## 0. 사전 확인

- [x] 평가 또는 제출 완료
- [x] GitHub `main` 에 최종 문서 병합 완료
- [x] 필요한 증빙 스크린샷 확보
- [x] HTTPS 와 `/health` 최종 동작 확인

## 1. DNS

- [x] No-IP 에서 `b0e2-b3.ddns.net` 호스트 삭제

```text
No-IP 콘솔 → My Services → DNS Records → 호스트 선택 → Remove
```

## 2. EC2 인스턴스

- [x] `b3-1-web-server` 종료
- [x] 상태가 `Terminated` 인지 확인

```text
EC2 콘솔 → 인스턴스 → 인스턴스 선택 → 인스턴스 상태 → 인스턴스 종료
```

```bash
aws ec2 terminate-instances --instance-ids <instance-id>
aws ec2 wait instance-terminated --instance-ids <instance-id>
```

## 3. 스토리지

- [x] 사용 중이 아닌 EBS 볼륨 삭제
- [x] 불필요한 스냅샷 삭제

```bash
aws ec2 describe-volumes --filters Name=status,Values=available \
  --query 'Volumes[].VolumeId' --output text
aws ec2 delete-volume --volume-id <volume-id>

aws ec2 describe-snapshots --owner-ids self \
  --query 'Snapshots[].SnapshotId' --output text
aws ec2 delete-snapshot --snapshot-id <snapshot-id>
```

## 4. 탄력적 IP

- [x] 할당된 주소 확인 후 반환

```bash
aws ec2 describe-addresses --query 'Addresses[].[PublicIp,AllocationId]' --output table
aws ec2 release-address --allocation-id <allocation-id>
```

## 5. 네트워크

- [x] 보안 그룹 삭제
- [x] 서브넷 삭제
- [x] 라우팅 테이블 삭제
- [x] 인터넷 게이트웨이 분리 및 삭제
- [x] VPC 삭제

콘솔에서는 VPC 삭제 시 연관 리소스를 함께 제거할 수 있습니다.

```text
VPC 콘솔 → VPC → 대상 선택 → 작업 → VPC 삭제
```

CLI 로 정리할 경우 순서가 중요합니다.

```bash
aws ec2 delete-security-group --group-id <sg-id>
aws ec2 delete-subnet --subnet-id <subnet-id>
aws ec2 delete-route-table --route-table-id <rtb-id>
aws ec2 detach-internet-gateway --internet-gateway-id <igw-id> --vpc-id <vpc-id>
aws ec2 delete-internet-gateway --internet-gateway-id <igw-id>
aws ec2 delete-vpc --vpc-id <vpc-id>
```

스크립트로 한 번에 정리할 수도 있습니다.

```bash
./scripts/teardown-infra.sh
```

## 6. 잔여 리소스 확인

- [x] 인스턴스 없음
- [x] EBS 볼륨 없음
- [x] 스냅샷 없음
- [x] 탄력적 IP 없음
- [x] NAT 게이트웨이 없음
- [x] 로드 밸런서 없음
- [x] 사용자 생성 VPC 없음

```bash
aws ec2 describe-instances --filters Name=tag:Project,Values=b3-1 \
  --query 'Reservations[].Instances[].[InstanceId,State.Name]' --output table
aws ec2 describe-volumes --query 'Volumes[].VolumeId' --output table
aws ec2 describe-addresses --query 'Addresses[].PublicIp' --output table
aws ec2 describe-vpcs --filters Name=tag:Project,Values=b3-1 \
  --query 'Vpcs[].VpcId' --output table
```

## 7. 비용 확인

- [x] 비용 탐색기에서 다음 날 비용이 발생하지 않는지 확인
- [x] 프리 티어 사용량 확인
- [x] 예산 알림 정리

```text
Billing and Cost Management → 비용 탐색기 → 일별
Billing and Cost Management → 프리 티어
```
