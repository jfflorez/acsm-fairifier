#!/usr/bin/env bash
set -euo pipefail
echo "[renku-start.sh] running as uid=$(id -u)" >&2
cd "/workspace/${MAIN_REPO}"

if [ "$(basename "$PWD")" = "${MAIN_REPO}" ] && [ -f app/data_flagging_app.py ]; then
  python app/data_flagging_app.py &
else
  echo "[start.sh] Not in ${MAIN_REPO} or app/data_flagging_app.py missing (PWD=$PWD); skipping Dash app." >&2
fi

BASE_URL="${RENKU_BASE_URL_PATH:-/}"

exec jupyter lab --ServerApp.ip=0.0.0.0 \
  --ServerApp.port=8888 \
  --ServerApp.base_url="$BASE_URL" \
  --ServerApp.token='' --ServerApp.password='' \
  --ServerApp.allow_root=true \
  --ServerApp.allow_remote_access=true \
  --ServerApp.allow_origin='*' \
  --ContentsManager.allow_hidden=true \
  --ServerApp.root_dir="/workspace/${MAIN_REPO}"