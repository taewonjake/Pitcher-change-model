#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: ./deploy/scripts/enable-https.sh <domain> <email>"
  exit 1
fi

DOMAIN="$1"
EMAIL="$2"

docker compose -f docker-compose.prod.yml up -d nginx certbot backend frontend

docker compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d "${DOMAIN}" -d "www.${DOMAIN}" \
  --email "${EMAIL}" \
  --agree-tos \
  --no-eff-email

sed "s/YOUR_DOMAIN/${DOMAIN}/g" deploy/nginx/nginx.https.conf > deploy/nginx/nginx.conf

docker compose -f docker-compose.prod.yml restart nginx

echo "HTTPS enabled for ${DOMAIN}"
