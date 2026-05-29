#!/usr/bin/env bash
set -euo pipefail

DEPLOY_PATH="${DEPLOY_PATH:-/opt/masterdoc-toir}"
SITE_HOST="${SITE_HOST:-toir.masterdoc.pro}"
WEB_ROOT="${WEB_ROOT:-/var/www/toir.masterdoc.pro}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-admin@masterdoc.pro}"
SITE="/etc/nginx/sites-available/${SITE_HOST}"

mkdir -p /var/www/certbot "${WEB_ROOT}"

if [[ -f "/etc/letsencrypt/live/${SITE_HOST}/fullchain.pem" ]]; then
  cp "${DEPLOY_PATH}/toir.masterdoc.pro.nginx.conf" "${SITE}"
else
  cp "${DEPLOY_PATH}/toir.masterdoc.pro.nginx.http.conf" "${SITE}"
fi

ln -sf "${SITE}" "/etc/nginx/sites-enabled/${SITE_HOST}"
nginx -t
systemctl reload nginx

if [[ ! -f "/etc/letsencrypt/live/${SITE_HOST}/fullchain.pem" ]]; then
  if certbot certonly --webroot -w /var/www/certbot \
    -d "${SITE_HOST}" \
    --non-interactive --agree-tos --email "${CERTBOT_EMAIL}"; then
    cp "${DEPLOY_PATH}/toir.masterdoc.pro.nginx.conf" "${SITE}"
    nginx -t
    systemctl reload nginx
  else
    echo "certbot skipped: add DNS A record for ${SITE_HOST}, then re-run deploy"
  fi
fi
