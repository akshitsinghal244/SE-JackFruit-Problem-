#!/usr/bin/env bash
# NFR-D1: the whole system must be ready within 120 s of `docker compose up`.  Usage: scripts/measure_startup.sh [compose args]
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose "$@" down -v >/dev/null 2>&1 || true
START=$(date +%s)
docker compose "$@" up -d --wait
END=$(date +%s)
echo "ready after $((END-START)) s (target <= 120 s)" | tee docs/perf/startup.txt
