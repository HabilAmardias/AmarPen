#!/usr/bin/env sh
set -eu

base="${1:-http://localhost:8080}"
curl -fsS "${base}/healthz"
echo
curl -fsS "${base}/api/v1/health"
echo
