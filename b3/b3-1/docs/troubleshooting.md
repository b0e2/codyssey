# Troubleshooting

## Docker Healthcheck가 `unhealthy`로 표시되는 문제

### 증상

웹 서비스는 정상적으로 응답하지만 Docker 컨테이너 상태가 `unhealthy`로 표시됐습니다.

### 원인

Healthcheck에서 `localhost`를 사용하면 실행 환경에 따라 IPv6 주소인 `::1`로 연결될 수 있습니다. 컨테이너 내부 Nginx는 해당 IPv6 요청을 처리하지 못했습니다.

### 해결

Dockerfile의 Healthcheck 주소를 `127.0.0.1`로 변경했습니다.

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget --quiet --tries=1 --spider \
    http://127.0.0.1/health || exit 1
```

### 결과

```text
healthy
```