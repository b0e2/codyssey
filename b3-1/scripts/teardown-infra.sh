#!/usr/bin/env bash
#
# b3-1 프로젝트 태그가 붙은 AWS 리소스를 삭제합니다.
# 평가와 증빙 확인이 끝난 뒤에 실행합니다.
#
# 삭제 순서
#   인스턴스 → 보안 그룹 → 서브넷 → 라우팅 테이블 → 인터넷 게이트웨이 → VPC
#
set -euo pipefail

REGION="${REGION:-ap-northeast-2}"
PROJECT="${PROJECT:-b3-1}"
FILTER="Name=tag:Project,Values=${PROJECT}"

echo "[1/7] 인스턴스 종료"
INSTANCE_IDS=$(aws ec2 describe-instances --region "${REGION}" \
  --filters "${FILTER}" "Name=instance-state-name,Values=pending,running,stopping,stopped" \
  --query 'Reservations[].Instances[].InstanceId' --output text)

if [ -n "${INSTANCE_IDS}" ]; then
  # shellcheck disable=SC2086
  aws ec2 terminate-instances --region "${REGION}" --instance-ids ${INSTANCE_IDS} >/dev/null
  # shellcheck disable=SC2086
  aws ec2 wait instance-terminated --region "${REGION}" --instance-ids ${INSTANCE_IDS}
  echo "    종료 완료: ${INSTANCE_IDS}"
else
  echo "    대상 없음"
fi

echo "[2/7] 탄력적 IP 반환"
for ALLOC in $(aws ec2 describe-addresses --region "${REGION}" \
  --filters "${FILTER}" --query 'Addresses[].AllocationId' --output text); do
  aws ec2 release-address --region "${REGION}" --allocation-id "${ALLOC}"
  echo "    반환: ${ALLOC}"
done

VPC_ID=$(aws ec2 describe-vpcs --region "${REGION}" \
  --filters "${FILTER}" --query 'Vpcs[0].VpcId' --output text)

if [ -z "${VPC_ID}" ] || [ "${VPC_ID}" = "None" ]; then
  echo "대상 VPC 없음. 종료합니다."
  exit 0
fi
echo "대상 VPC: ${VPC_ID}"

echo "[3/7] 보안 그룹 삭제"
for SG in $(aws ec2 describe-security-groups --region "${REGION}" \
  --filters "Name=vpc-id,Values=${VPC_ID}" \
  --query "SecurityGroups[?GroupName!='default'].GroupId" --output text); do
  aws ec2 delete-security-group --region "${REGION}" --group-id "${SG}"
  echo "    삭제: ${SG}"
done

echo "[4/7] 서브넷 삭제"
for SUBNET in $(aws ec2 describe-subnets --region "${REGION}" \
  --filters "Name=vpc-id,Values=${VPC_ID}" \
  --query 'Subnets[].SubnetId' --output text); do
  aws ec2 delete-subnet --region "${REGION}" --subnet-id "${SUBNET}"
  echo "    삭제: ${SUBNET}"
done

echo "[5/7] 라우팅 테이블 삭제"
for RTB in $(aws ec2 describe-route-tables --region "${REGION}" \
  --filters "Name=vpc-id,Values=${VPC_ID}" \
  --query 'RouteTables[?length(Associations[?Main==`true`])==`0`].RouteTableId' --output text); do
  aws ec2 delete-route-table --region "${REGION}" --route-table-id "${RTB}"
  echo "    삭제: ${RTB}"
done

echo "[6/7] 인터넷 게이트웨이 분리 및 삭제"
for IGW in $(aws ec2 describe-internet-gateways --region "${REGION}" \
  --filters "Name=attachment.vpc-id,Values=${VPC_ID}" \
  --query 'InternetGateways[].InternetGatewayId' --output text); do
  aws ec2 detach-internet-gateway --region "${REGION}" --internet-gateway-id "${IGW}" --vpc-id "${VPC_ID}"
  aws ec2 delete-internet-gateway --region "${REGION}" --internet-gateway-id "${IGW}"
  echo "    삭제: ${IGW}"
done

echo "[7/7] VPC 삭제"
aws ec2 delete-vpc --region "${REGION}" --vpc-id "${VPC_ID}"
echo "    삭제: ${VPC_ID}"

cat <<'SUMMARY'

삭제 완료. 아래 명령으로 잔여 리소스를 확인하세요.

  aws ec2 describe-instances --filters Name=tag:Project,Values=b3-1 \
    --query 'Reservations[].Instances[].[InstanceId,State.Name]' --output table
  aws ec2 describe-volumes --query 'Volumes[].VolumeId' --output table
  aws ec2 describe-addresses --query 'Addresses[].PublicIp' --output table
  aws ec2 describe-vpcs --filters Name=tag:Project,Values=b3-1 \
    --query 'Vpcs[].VpcId' --output table
SUMMARY
