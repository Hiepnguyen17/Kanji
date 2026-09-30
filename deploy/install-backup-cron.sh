#!/bin/sh
# Install or replace the single KanjiAI daily SQLite backup cron entry.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
SCHEDULE=${KANJIAI_BACKUP_CRON:-'15 3 * * *'}
KEEP=${KANJIAI_BACKUP_KEEP:-14}
MARKER='# KanjiAI SQLite backup'

case "$KEEP" in
  ''|*[!0-9]*) echo 'KANJIAI_BACKUP_KEEP must be an integer from 1 to 365' >&2; exit 1 ;;
esac
if [ "$KEEP" -lt 1 ] || [ "$KEEP" -gt 365 ]; then
  echo 'KANJIAI_BACKUP_KEEP must be an integer from 1 to 365' >&2
  exit 1
fi

# Cron opens its log file before backup-sqlite.sh can create this directory.
if [ -L "$ROOT/backups" ]; then
  echo 'Refusing symlinked backups directory' >&2
  exit 1
fi
mkdir -p "$ROOT/backups"
chmod 700 "$ROOT/backups"

CRON_LINE="$SCHEDULE cd $ROOT && KANJIAI_BACKUP_KEEP=$KEEP /bin/sh $ROOT/deploy/backup-sqlite.sh >> $ROOT/backups/backup-cron.log 2>&1 $MARKER"
TEMP_FILE=$(mktemp)
trap 'rm -f "$TEMP_FILE"' EXIT HUP INT TERM

(crontab -l 2>/dev/null || true) | grep -v -F "$MARKER" > "$TEMP_FILE" || true
printf '%s\n' "$CRON_LINE" >> "$TEMP_FILE"
crontab "$TEMP_FILE"

echo "Installed: $SCHEDULE (server local time)"
echo "Retention: newest $KEEP database backups"
echo "Log: $ROOT/backups/backup-cron.log"
crontab -l | grep -F "$MARKER"
