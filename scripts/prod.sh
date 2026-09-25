#!/usr/bin/env bash
set -euo pipefail

exec .venv/bin/gunicorn \
	--config deploy/gunicorn/gunicorn.conf.py \
	personal_site_backend.main:app
