#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: ./deploy/scripts/enable-https.sh <domain> <email>"
  exit 1
fi

DOMAIN="$1"
EMAIL="$2"

if docker compose version >/dev/null 2>&1; then
  compose() { docker compose -f docker-compose.prod.yml "$@"; }
elif docker-compose --version >/dev/null 2>&1; then
  compose() { docker-compose -f docker-compose.prod.yml "$@"; }
else
  echo "Docker Compose is not installed."
  exit 1
fi

compose up -d nginx certbot backend frontend

compose run --rm --entrypoint certbot certbot certonly \
  --webroot -w /var/www/certbot \
  -d "${DOMAIN}" -d "www.${DOMAIN}" \
  --email "${EMAIL}" \
  --agree-tos \
  --no-eff-email \
  --keep-until-expiring

sed "s/YOUR_DOMAIN/${DOMAIN}/g" deploy/nginx/nginx.https.conf > deploy/nginx/nginx.conf

compose restart nginx

echo "HTTPS enabled for ${DOMAIN}"
