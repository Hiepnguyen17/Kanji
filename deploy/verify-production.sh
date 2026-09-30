#!/bin/sh
# Verify deployment wiring without printing any secret values.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
ENV_FILE="$ROOT/deploy/.env.production"

if [ ! -f "$ENV_FILE" ]; then
  echo "FAIL: missing deploy/.env.production"
  exit 1
fi

value_of() {
  sed -n "s/^$1=//p" "$ENV_FILE" | tail -n 1 | tr -d '\r'
}

required='KANJIAI_DB_PATH KANJIAI_CORS_ORIGINS KANJIAI_APP_URL GOOGLE_CLIENT_ID GOOGLE_CLIENT_SECRET GOOGLE_REDIRECT_URI KANJIAI_ADMIN_API_KEY CLOUDFLARE_TUNNEL_TOKEN'
failed=0
for name in $required; do
  value=$(value_of "$name")
  case "$value" in
    ''|*replace-with-*|*example.com*) echo "FAIL: $name is missing or still a placeholder"; failed=1 ;;
    *) echo "OK: $name is set" ;;
  esac
done

app_url=$(value_of KANJIAI_APP_URL)
redirect_uri=$(value_of GOOGLE_REDIRECT_URI)
origins=$(value_of KANJIAI_CORS_ORIGINS)
expected_redirect="${app_url%/}/auth/google/callback"

if [ "$redirect_uri" = "$expected_redirect" ]; then
  echo "OK: Google callback matches KANJIAI_APP_URL"
else
  echo "FAIL: Google callback does not match KANJIAI_APP_URL"
  failed=1
fi

case ",$origins," in
  *,"$app_url",*) echo "OK: production origin is present in CORS allowlist" ;;
  *) echo "FAIL: KANJIAI_APP_URL is absent from CORS allowlist"; failed=1 ;;
esac

if docker compose --project-directory "$ROOT" --env-file "$ENV_FILE" config --quiet; then
  echo "OK: Docker Compose configuration is valid"
else
  echo "FAIL: Docker Compose configuration is invalid"
  failed=1
fi

if [ "$failed" -ne 0 ]; then
  exit 1
fi
