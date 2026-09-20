# Cleanup Checklist

평가와 증빙 확인이 모두 완료된 후 진행합니다.

## Before Cleanup

- [ ] GitHub `main`에 최종 문서가 병합됐는지 확인
- [ ] HTTPS 메인 페이지 접속 확인
- [ ] `/health` 응답 확인
- [ ] 필요한 스크린샷 저장
- [ ] 평가 또는 제출 완료 확인

## DNS

- [ ] No-IP에서 `b0e2-b3.ddns.net` 호스트 삭제
- [ ] DNS 레코드가 더 이상 사용되지 않는지 확인

## EC2

- [ ] `b3-1-web-server` 인스턴스 종료
- [ ] 인스턴스 상태가 `Terminated`인지 확인
- [ ] 연결된 네트워크 인터페이스가 제거됐는지 확인

## Storage

- [ ] 사용하지 않는 EBS 볼륨 삭제
- [ ] 불필요한 EBS 스냅샷 삭제

## Public IP

- [ ] Elastic IP 할당 여부 확인
- [ ] 할당된 Elastic IP가 있다면 연결 해제 후 반환

## Network

- [ ] 사용자 생성 Security Group 삭제
- [ ] Route Table의 Subnet 연결 해제
- [ ] 사용자 생성 Route Table 삭제
- [ ] Public Subnet 삭제
- [ ] Internet Gateway를 VPC에서 분리
- [ ] Internet Gateway 삭제
- [ ] VPC 삭제

## Billing

서울 리전 `ap-northeast-2`에서 다음 리소스가 남아 있지 않은지 확인합니다.

- [ ] EC2 인스턴스
- [ ] EBS 볼륨
- [ ] EBS 스냅샷
- [ ] Elastic IP
- [ ] NAT Gateway
- [ ] Load Balancer
- [ ] 사용자 생성 VPC

마지막으로 AWS Billing과 Cost Explorer에서 잔여 비용을 확인합니다.
