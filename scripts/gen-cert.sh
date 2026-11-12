#!/usr/bin/env bash
# Self-signed development certificate for https://localhost (US-23.1). certs/ is git-ignored.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p certs
openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout certs/rdcp.key -out certs/rdcp.crt -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
chmod 644 certs/rdcp.key certs/rdcp.crt   # readable by the nginx container; dev certificate only
echo "created certs/rdcp.crt and certs/rdcp.key (browser will warn: self-signed)"
