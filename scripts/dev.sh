#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIRECTORY/.." && pwd)"
NGINX_CONTAINER="personal-site-nginx-dev"
NGINX_CONFIG="$PROJECT_ROOT/deploy/nginx/personal-site.local.conf"

if command -v cygpath >/dev/null 2>&1; then
	NGINX_CONFIG="$(cygpath -w "$NGINX_CONFIG")"
fi

cd "$PROJECT_ROOT"

uv run fastapi dev src/personal_site_backend/main.py &
FASTAPI_PID=$!

cleanup() {
	docker rm -f "$NGINX_CONTAINER" 2>/dev/null || true
	kill "$FASTAPI_PID" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

docker rm -f "$NGINX_CONTAINER" 2>/dev/null || true

MSYS_NO_PATHCONV=1 docker run --rm \
	--name "$NGINX_CONTAINER" \
	--publish 8080:80 \
	--mount "type=bind,source=$NGINX_CONFIG,target=/etc/nginx/nginx.conf,readonly" \
	nginx:alpine