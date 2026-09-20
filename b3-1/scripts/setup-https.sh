#!/usr/bin/env bash
#
# 도메인 연결 후 HTTPS 를 적용합니다. EC2 인스턴스에서 실행합니다.
#
# 사전 조건
#   1. DNS A 레코드가 인스턴스 공인 IP 를 가리킬 것
#   2. 보안 그룹에서 80, 443 이 열려 있을 것
#
# 사용 예
#   DOMAIN=b0e2-b3.ddns.net EMAIL=me@example.com ./scripts/setup-https.sh
#
set -euo pipefail

DOMAIN="${DOMAIN:?DOMAIN 환경 변수가 필요합니다}"
EMAIL="${EMAIL:?EMAIL 환경 변수가 필요합니다}"

echo "[1/4] DNS 확인"
RESOLVED=$(getent hosts "${DOMAIN}" | awk '{print $1}' | head -1)
PUBLIC_IP=$(curl -fsS http://169.254.169.254/latest/meta-data/public-ipv4 \
  -H "X-aws-ec2-metadata-token: $(curl -fsS -X PUT http://169.254.169.254/latest/api/token \
  -H 'X-aws-ec2-metadata-token-ttl-seconds: 60')")
echo "    도메인 응답 IP: ${RESOLVED}"
echo "    인스턴스 공인 IP: ${PUBLIC_IP}"

if [ "${RESOLVED}" != "${PUBLIC_IP}" ]; then
  echo "    경고: DNS 가 아직 인스턴스를 가리키지 않습니다."
fi

echo "[2/4] 인증서 발급"
sudo certbot --nginx \
  -d "${DOMAIN}" \
  --non-interactive \
  --agree-tos \
  --email "${EMAIL}" \
  --redirect

echo "[3/4] 자동 갱신 점검"
sudo certbot renew --dry-run

echo "[4/4] 응답 확인"
curl -si "https://${DOMAIN}/health" | head -5
curl -sI "http://${DOMAIN}" | head -5
