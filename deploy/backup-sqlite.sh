#!/bin/sh
set -eu
umask 077

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
NAME="kanjiai-${TIMESTAMP}.db"
CONTAINER_PATH="/tmp/${NAME}"
if [ -L "$ROOT/backups" ]; then
  echo 'Refusing symlinked backups directory' >&2
  exit 1
fi
mkdir -p "$ROOT/backups"
chmod 700 "$ROOT/backups"

compose() {
  docker compose --project-directory "$ROOT" --env-file "$ROOT/deploy/.env.production" "$@"
}

compose exec -T api python /app/deploy/backup_sqlite.py \
  --source /data/kanjiai.db \
  --output "$CONTAINER_PATH"

CONTAINER_ID=$(compose ps -q api)
docker cp "${CONTAINER_ID}:${CONTAINER_PATH}" "$ROOT/backups/${NAME}"
chmod 600 "$ROOT/backups/${NAME}"
compose exec -T api rm -f "$CONTAINER_PATH"
python3 "$ROOT/deploy/verify_backup.py" --backup "$ROOT/backups/${NAME}"
python3 "$ROOT/deploy/prune_backups.py" --directory "$ROOT/backups" --keep "${KANJIAI_BACKUP_KEEP:-14}"
printf '%s\n' "$ROOT/backups/${NAME}"
