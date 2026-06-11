#!/usr/bin/env bash
set -euo pipefail

DEPLOY_PATH="${DEPLOY_PATH:-/opt/masterdoc-toir}"
SITE_HOST="${SITE_HOST:-fixaverse.ru}"
WEB_ROOT="${WEB_ROOT:-/var/www/fixaverse.ru}"
REDIRECT_HOST="${REDIRECT_HOST:-toir.masterdoc.pro}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-admin@masterdoc.pro}"

install_site() {
  local host="$1"
  local https_conf="$2"
  local http_conf="$3"
  local site="/etc/nginx/sites-available/${host}"

  if [[ -f "/etc/letsencrypt/live/${host}/fullchain.pem" ]]; then
    cp "${DEPLOY_PATH}/${https_conf}" "${site}"
  else
    cp "${DEPLOY_PATH}/${http_conf}" "${site}"
  fi

  ln -sf "${site}" "/etc/nginx/sites-enabled/${host}"

  if [[ ! -f "/etc/letsencrypt/live/${host}/fullchain.pem" ]]; then
    if certbot certonly --webroot -w /var/www/certbot \
      -d "${host}" \
      --non-interactive --agree-tos --email "${CERTBOT_EMAIL}"; then
      cp "${DEPLOY_PATH}/${https_conf}" "${site}"
    else
      echo "certbot skipped for ${host}: add DNS A record, then re-run deploy"
    fi
  fi
}

mkdir -p /var/www/certbot "${WEB_ROOT}"

install_site "${SITE_HOST}" "fixaverse.ru.nginx.conf" "fixaverse.ru.nginx.http.conf"

redirect_site="/etc/nginx/sites-available/${REDIRECT_HOST}"
cp "${DEPLOY_PATH}/toir.masterdoc.pro.redirect.nginx.conf" "${redirect_site}"
ln -sf "${redirect_site}" "/etc/nginx/sites-enabled/${REDIRECT_HOST}"

nginx -t
systemctl reload nginx
