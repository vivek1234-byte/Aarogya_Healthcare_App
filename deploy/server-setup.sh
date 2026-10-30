#!/usr/bin/env bash
# Runs on the server as root (deploy.sh pipes it over SSH). Installs or updates ArogyaSaathi
# from /tmp/arogya.tgz, then (re)starts the app behind Caddy with HTTPS for $DOMAIN.
set -euo pipefail

DOMAIN="${DOMAIN:?DOMAIN is required}"
APP=/opt/arogya
STAGE="$(mktemp -d)"
tar xzf /tmp/arogya.tgz -C "$STAGE"

id arogya >/dev/null 2>&1 || useradd --system --create-home --home-dir "$APP" arogya
mkdir -p "$APP/backend/storage_data" /var/lib/arogya /var/backups/arogya

# The server keeps its own .env after the first deploy: it holds the encryption key for existing patient data
if [ -f "$APP/backend/.env" ]; then
  cp "$APP/backend/.env" "$STAGE/backend/.env"
else
  set_env() {
    if grep -q "^$1=" "$STAGE/backend/.env"; then
      sed -i "s|^$1=.*|$1=\"$2\"|" "$STAGE/backend/.env"
    else
      echo "$1=\"$2\"" >> "$STAGE/backend/.env"
    fi
  }
  set_env PORT 8080
  set_env HOST 127.0.0.1
  set_env AROGYA_DB_PATH /var/lib/arogya/arogya.db
fi

# Replace code, keep the virtualenv and data
rm -rf "$APP/backend/app" "$APP/frontend"
cp -a "$STAGE/backend/." "$APP/backend/"
cp -a "$STAGE/frontend" "$APP/"
chown -R arogya: "$APP" /var/lib/arogya /var/backups/arogya
chmod 600 "$APP/backend/.env"

[ -x "$APP/backend/.venv/bin/python" ] || sudo -u arogya python3 -m venv "$APP/backend/.venv"
sudo -u arogya "$APP/backend/.venv/bin/pip" install -q --upgrade pip
sudo -u arogya "$APP/backend/.venv/bin/pip" install -q -r "$APP/backend/requirements-server.txt"

install -m 644 "$STAGE/deploy/arogya.service" /etc/systemd/system/arogya.service

cat > /etc/caddy/Caddyfile <<EOF
$DOMAIN {
	encode gzip
	reverse_proxy 127.0.0.1:8080
}
EOF

# Daily database backup at 02:30, keep 14 days
cat > /etc/cron.d/arogya-backup <<'EOF'
30 2 * * * arogya sqlite3 /var/lib/arogya/arogya.db ".backup /var/backups/arogya/arogya-$(date +\%F).db" && find /var/backups/arogya -name 'arogya-*.db' -mtime +14 -delete
EOF

systemctl daemon-reload
systemctl enable arogya >/dev/null 2>&1
systemctl restart arogya
systemctl reload caddy

for _ in $(seq 1 15); do
  curl -fsS http://127.0.0.1:8080/api/v1/health >/dev/null 2>&1 && break
  sleep 1
done
echo "App health: $(curl -fsS http://127.0.0.1:8080/api/v1/health)"
rm -rf "$STAGE" /tmp/arogya.tgz
echo "Deployed: https://$DOMAIN"
