#!/usr/bin/env bash
set -euo pipefail

export $(grep -v '^#' .env 2>/dev/null | xargs -r)

uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
