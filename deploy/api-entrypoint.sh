#!/bin/sh
set -eu

: "${KANJIAI_DB_PATH:=/data/kanjiai.db}"
export KANJIAI_DB_PATH

if [ ! -f "$KANJIAI_DB_PATH" ]; then
  mkdir -p "$(dirname "$KANJIAI_DB_PATH")"
  cp /app/backend/kanjiai.db "$KANJIAI_DB_PATH"
fi

exec "$@"