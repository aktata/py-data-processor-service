#!/usr/bin/env bash
set -euo pipefail

export $(grep -v '^#' .env 2>/dev/null | xargs -r)

python -m app.cli --help
