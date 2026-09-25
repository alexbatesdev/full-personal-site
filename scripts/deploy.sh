#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ "$(id -u)" -ne 0 ]]; then
	echo "Run this script as root so it can restart the systemd service." >&2
	exit 1
fi

runuser -u personal-site -- git fetch origin master
runuser -u personal-site -- git checkout master
runuser -u personal-site -- git pull --ff-only origin master
runuser -u personal-site -- git submodule update --init --recursive

runuser -u personal-site -- uv sync --no-dev
systemctl restart personal-site-backend