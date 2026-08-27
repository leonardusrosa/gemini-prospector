#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${PROSPECTOR_REPO_DIR:-/opt/gemini-prospector}"
DATA_DIR="${PROSPECTOR_DATA_DIR:-/var/lib/prospector-dashboard}"
SERVICE_SRC="$REPO_DIR/deploy/phoenix/prospector-dashboard.service"
SERVICE_DST="/etc/systemd/system/prospector-dashboard.service"
ENV_DST="/etc/prospector-dashboard.env"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root (or with sudo)." >&2
  exit 1
fi

if [ ! -d "$REPO_DIR/.git" ]; then
  echo "Git checkout not found at $REPO_DIR." >&2
  echo "Set PROSPECTOR_REPO_DIR to the existing Phoenix checkout and rerun." >&2
  exit 1
fi

if ! id prospector >/dev/null 2>&1; then
  useradd --system --home "$DATA_DIR" --shell /usr/sbin/nologin prospector
fi

install -d -m 0700 -o prospector -g prospector "$DATA_DIR"

cd "$REPO_DIR"
git fetch origin
git pull --ff-only origin main

install -m 0644 "$SERVICE_SRC" "$SERVICE_DST"
systemctl daemon-reload
systemctl enable prospector-dashboard.service >/dev/null

if [ ! -f "$ENV_DST" ]; then
  install -m 0600 "$REPO_DIR/deploy/phoenix/prospector-dashboard.env.example" "$ENV_DST"
  echo "Created $ENV_DST from the example. Fill in the real auth password and Evolution API key before starting." >&2
  exit 2
fi
chmod 0600 "$ENV_DST"

if [ ! -f "$DATA_DIR/prospector.db" ]; then
  echo "Canonical CRM database missing: $DATA_DIR/prospector.db" >&2
  echo "Copy the current local prospector.db securely to this path before starting the service." >&2
  exit 3
fi

chown prospector:prospector "$DATA_DIR/prospector.db"
chmod 0600 "$DATA_DIR/prospector.db"
if [ -f "$DATA_DIR/prospector-config.json" ]; then
  chown prospector:prospector "$DATA_DIR/prospector-config.json"
  chmod 0600 "$DATA_DIR/prospector-config.json"
fi

systemctl restart prospector-dashboard.service
sleep 1
systemctl --no-pager --full status prospector-dashboard.service

if command -v curl >/dev/null 2>&1; then
  curl -fsS http://127.0.0.1:8765/api/health >/dev/null
  echo "Health check: PASS"
fi

echo "Phoenix dashboard backend updated and running on 127.0.0.1:8765."
