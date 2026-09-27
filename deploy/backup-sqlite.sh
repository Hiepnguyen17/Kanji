#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
NAME="kanjiai-${TIMESTAMP}.db"
CONTAINER_PATH="/tmp/${NAME}"
mkdir -p "$ROOT/backups"

compose() {
  docker compose --project-directory "$ROOT" --env-file "$ROOT/deploy/.env.production" "$@"
}

compose exec -T api python /app/deploy/backup_sqlite.py \
  --source /data/kanjiai.db \
  --output "$CONTAINER_PATH"

CONTAINER_ID=$(compose ps -q api)
docker cp "${CONTAINER_ID}:${CONTAINER_PATH}" "$ROOT/backups/${NAME}"
compose exec -T api rm -f "$CONTAINER_PATH"
printf '%s\n' "$ROOT/backups/${NAME}"