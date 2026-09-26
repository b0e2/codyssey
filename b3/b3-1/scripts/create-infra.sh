#!/usr/bin/env bash
#
# b3-1 네트워크와 웹 서버를 생성합니다.
# AWS CloudShell 또는 AWS CLI 가 구성된 환경에서 실행합니다.
#
# 사용 예
#   SSH_CIDR=203.0.113.10/32 ./scripts/create-infra.sh
#
set -euo pipefail

REGION="${REGION:-ap-northeast-2}"
AZ="${AZ:-ap-northeast-2a}"
PROJECT="${PROJECT:-b3-1}"
KEY_NAME="${KEY_NAME:-b3-1-key}"
INSTANCE_TYPE="${INSTANCE_TYPE:-t3.micro}"
VPC_CIDR="${VPC_CIDR:-10.0.0.0/16}"
SUBNET_CIDR="${SUBNET_CIDR:-10.0.1.0/24}"
SSH_CIDR="${SSH_CIDR:?SSH_CIDR 환경 변수가 필요합니다. 예: 203.0.113.10/32}"
PROVISION_URL="${PROVISION_URL:-https://raw.githubusercontent.com/b0e2/codyssey/main/b3/b3-1/scripts/provision.sh}"

COMMON_TAGS="{Key=Project,Value=${PROJECT}},{Key=Env,Value=lab},{Key=Owner,Value=jeongbeen},{Key=ManagedBy,Value=create-infra-script}"

echo "[1/8] VPC 생성"
VPC_ID=$(aws ec2 create-vpc \
  --region "${REGION}" \
  --cidr-block "${VPC_CIDR}" \
  --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=${PROJECT}-vpc},${COMMON_TAGS}]" \
  --query 'Vpc.VpcId' --output text)
aws ec2 modify-vpc-attribute --region "${REGION}" --vpc-id "${VPC_ID}" --enable-dns-hostnames
echo "    VPC_ID=${VPC_ID}"

echo "[2/8] 퍼블릭 서브넷 생성"
SUBNET_ID=$(aws ec2 create-subnet \
  --region "${REGION}" \
  --vpc-id "${VPC_ID}" \
  --cidr-block "${SUBNET_CIDR}" \
  --availability-zone "${AZ}" \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT}-public-subnet-a},${COMMON_TAGS}]" \
  --query 'Subnet.SubnetId' --output text)
aws ec2 modify-subnet-attribute --region "${REGION}" --subnet-id "${SUBNET_ID}" --map-public-ip-on-launch
echo "    SUBNET_ID=${SUBNET_ID}"

echo "[3/8] 인터넷 게이트웨이 생성 및 연결"
IGW_ID=$(aws ec2 create-internet-gateway \
  --region "${REGION}" \
  --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=${PROJECT}-igw},${COMMON_TAGS}]" \
  --query 'InternetGateway.InternetGatewayId' --output text)
aws ec2 attach-internet-gateway --region "${REGION}" --vpc-id "${VPC_ID}" --internet-gateway-id "${IGW_ID}"
echo "    IGW_ID=${IGW_ID}"

echo "[4/8] 라우팅 테이블 생성 및 기본 경로 설정"
RTB_ID=$(aws ec2 create-route-table \
  --region "${REGION}" \
  --vpc-id "${VPC_ID}" \
  --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=${PROJECT}-public-rt},${COMMON_TAGS}]" \
  --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-route --region "${REGION}" \
  --route-table-id "${RTB_ID}" \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id "${IGW_ID}" >/dev/null
aws ec2 associate-route-table --region "${REGION}" \
  --route-table-id "${RTB_ID}" \
  --subnet-id "${SUBNET_ID}" >/dev/null
echo "    RTB_ID=${RTB_ID}"

echo "[5/8] 보안 그룹 생성"
SG_ID=$(aws ec2 create-security-group \
  --region "${REGION}" \
  --group-name "${PROJECT}-web-sg" \
  --description "Security group for ${PROJECT} web server" \
  --vpc-id "${VPC_ID}" \
  --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=${PROJECT}-web-sg},${COMMON_TAGS}]" \
  --query 'GroupId' --output text)

aws ec2 authorize-security-group-ingress --region "${REGION}" --group-id "${SG_ID}" \
  --ip-permissions \
    "IpProtocol=tcp,FromPort=80,ToPort=80,IpRanges=[{CidrIp=0.0.0.0/0,Description=Public HTTP access}]" \
    "IpProtocol=tcp,FromPort=443,ToPort=443,IpRanges=[{CidrIp=0.0.0.0/0,Description=Public HTTPS access}]" \
    "IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges=[{CidrIp=${SSH_CIDR},Description=SSH from my IP}]" >/dev/null
echo "    SG_ID=${SG_ID}"

echo "[6/8] Ubuntu 24.04 AMI 조회"
AMI_ID=$(aws ssm get-parameters --region "${REGION}" \
  --names /aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id \
  --query 'Parameters[0].Value' --output text 2>/dev/null || true)

if [ -z "${AMI_ID}" ] || [ "${AMI_ID}" = "None" ]; then
  AMI_ID=$(aws ec2 describe-images --region "${REGION}" \
    --owners 099720109477 \
    --filters "Name=name,Values=ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*" \
              "Name=state,Values=available" \
    --query 'sort_by(Images,&CreationDate)[-1].ImageId' --output text)
fi
echo "    AMI_ID=${AMI_ID}"

echo "[7/8] 인스턴스 생성"
USER_DATA_FILE=$(mktemp)
curl -fsSL "${PROVISION_URL}" -o "${USER_DATA_FILE}"

INSTANCE_ID=$(aws ec2 run-instances --region "${REGION}" \
  --image-id "${AMI_ID}" \
  --instance-type "${INSTANCE_TYPE}" \
  --key-name "${KEY_NAME}" \
  --subnet-id "${SUBNET_ID}" \
  --security-group-ids "${SG_ID}" \
  --user-data "file://${USER_DATA_FILE}" \
  --metadata-options "HttpTokens=required,HttpEndpoint=enabled" \
  --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=8,VolumeType=gp3,DeleteOnTermination=true}" \
  --tag-specifications \
    "ResourceType=instance,Tags=[{Key=Name,Value=${PROJECT}-web-server},${COMMON_TAGS}]" \
    "ResourceType=volume,Tags=[{Key=Name,Value=${PROJECT}-web-root},${COMMON_TAGS}]" \
  --query 'Instances[0].InstanceId' --output text)
echo "    INSTANCE_ID=${INSTANCE_ID}"

echo "[8/8] 인스턴스 기동 대기"
aws ec2 wait instance-running --region "${REGION}" --instance-ids "${INSTANCE_ID}"
PUBLIC_IP=$(aws ec2 describe-instances --region "${REGION}" \
  --instance-ids "${INSTANCE_ID}" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

cat <<SUMMARY

생성 완료
  VPC          : ${VPC_ID}
  Subnet       : ${SUBNET_ID}
  IGW          : ${IGW_ID}
  Route Table  : ${RTB_ID}
  Security Grp : ${SG_ID}
  Instance     : ${INSTANCE_ID}
  Public IP    : ${PUBLIC_IP}

다음 단계
  1. DNS A 레코드를 ${PUBLIC_IP} 로 변경
  2. 인스턴스에서 scripts/setup-https.sh 실행
SUMMARY
