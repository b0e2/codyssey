FROM nginx:alpine

COPY app/index.html /usr/share/nginx/html/index.html
COPY nginx/site.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1
