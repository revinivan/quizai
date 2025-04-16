#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

exec uv run gunicorn -w 2 -b 0.0.0.0:"${PORT:-3000}" main:app
