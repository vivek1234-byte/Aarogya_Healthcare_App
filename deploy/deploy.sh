#!/usr/bin/env bash
# Deploy (or update) ArogyaSaathi on the AWS Lightsail server.
# Usage: deploy/deploy.sh [ssh-target] [domain]
#   defaults: ubuntu@16.4.93.27  16-4-93-27.sslip.io
# The SSH key path can be overridden with KEY=/path/to/key.pem
set -euo pipefail

TARGET="${1:-ubuntu@16.4.93.27}"
DOMAIN="${2:-16-4-93-27.sslip.io}"
KEY="${KEY:-$HOME/Downloads/LightsailDefaultKey-ap-south-1.pem}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUNDLE="$(mktemp -d)/arogya.tgz"

echo "Packing app..."
tar czf "$BUNDLE" -C "$ROOT" \
  --exclude='__pycache__' --exclude='frontend/lib' --exclude='frontend/android' --exclude='frontend/web' \
  backend/app backend/.env backend/requirements-server.txt frontend deploy/arogya.service

echo "Uploading to $TARGET..."
scp -i "$KEY" -q "$BUNDLE" "$TARGET:/tmp/arogya.tgz"
rm -f "$BUNDLE"

echo "Installing on server..."
ssh -i "$KEY" "$TARGET" "sudo DOMAIN='$DOMAIN' bash -s" < "$ROOT/deploy/server-setup.sh"
