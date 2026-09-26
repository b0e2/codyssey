#!/usr/bin/env bash
#
# EC2 인스턴스 초기 구성 스크립트입니다.
# run-instances 의 --user-data 로 전달되어 루트 권한으로 실행됩니다.
#
# 수행 작업
#   1. Docker, Nginx, Certbot 설치
#   2. 애플리케이션 저장소 클론 및 이미지 빌드
#   3. 컨테이너를 127.0.0.1:8080 으로만 노출
#   4. 호스트 Nginx 리버스 프록시 구성
#
set -euxo pipefail

REPO_URL="https://github.com/b0e2/codyssey.git"
APP_DIR="/opt/b3-1"
IMAGE_TAG="b3-1-web:1.4"
CONTAINER_NAME="b3-1-web"

export DEBIAN_FRONTEND=noninteractive

apt-get update -y
apt-get install -y docker.io nginx git certbot python3-certbot-nginx

systemctl enable --now docker
systemctl enable --now nginx
usermod -aG docker ubuntu || true

rm -rf "${APP_DIR}"
git clone "${REPO_URL}" "${APP_DIR}"
cd "${APP_DIR}/b3/b3-1"

docker build -t "${IMAGE_TAG}" .

docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true
docker run -d \
  --name "${CONTAINER_NAME}" \
  --restart unless-stopped \
  -p 127.0.0.1:8080:80 \
  "${IMAGE_TAG}"

cat > /etc/nginx/sites-available/b3-1 <<'NGINX'
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/b3-1 /etc/nginx/sites-enabled/b3-1
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl reload nginx

echo "provision completed" > /var/log/b3-1-provision.done
