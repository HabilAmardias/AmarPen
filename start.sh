#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

COMPOSE=(docker compose)
BUILD=1
FOREGROUND=0
BOOTSTRAP=0
ACTION="up"

usage() {
  cat <<'EOF'
AI-Assisted Pentest Platform entrypoint

Usage:
  ./start.sh [options]

Starts the complete local stack:
  db, s3, mock-llm, backend, worker, frontend

Options:
  --no-build       Use existing images instead of rebuilding
  --foreground     Run attached and stream logs
  --bootstrap      Prompt for the initial administrator after health checks
  --stop           Stop the stack (volumes are retained)
  --reset          Stop the stack and delete its volumes
  --logs           Follow service logs
  --status         Show service status
  -h, --help       Show this help

Environment:
  ADMIN_USERNAME   Bootstrap username (default: admin)
  ADMIN_PASSWORD   Bootstrap password (prompted when --bootstrap is used)
  FRONTEND_PORT    Frontend port for health checks (default: 8080)
  BACKEND_PORT     Backend port for health checks (default: 8000)
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --no-build) BUILD=0 ;;
    --foreground) FOREGROUND=1 ;;
    --bootstrap) BOOTSTRAP=1 ;;
    --stop) ACTION="stop" ;;
    --reset) ACTION="reset" ;;
    --logs) ACTION="logs" ;;
    --status) ACTION="status" ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required but was not found in PATH." >&2
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required for health checks and bootstrap." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose v2 is required (docker compose)." >&2
  exit 1
fi

case "$ACTION" in
  stop)
    "${COMPOSE[@]}" down
    echo "Platform stopped. Volumes retained."
    exit 0
    ;;
  reset)
    "${COMPOSE[@]}" down -v
    echo "Platform stopped and volumes removed."
    exit 0
    ;;
  logs)
    "${COMPOSE[@]}" logs -f
    exit 0
    ;;
  status)
    "${COMPOSE[@]}" ps
    exit 0
    ;;
esac

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example."
  echo "Review SECRET_KEY, AUDIT_ANCHOR_KEY, BOOTSTRAP_TOKEN, and storage credentials before production use."
fi

FRONTEND_PORT="${FRONTEND_PORT:-8080}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

if [ "$FOREGROUND" -eq 1 ]; then
  if [ "$BUILD" -eq 1 ]; then
    exec "${COMPOSE[@]}" up --build
  fi
  exec "${COMPOSE[@]}" up
fi

if [ "$BUILD" -eq 1 ]; then
  "${COMPOSE[@]}" up -d --build
else
  "${COMPOSE[@]}" up -d
fi

wait_for_health() {
  local url="$1"
  local attempts="${2:-60}"
  local i=1
  while [ "$i" -le "$attempts" ]; do
    if curl -fsS --max-time 3 "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
    i=$((i + 1))
  done
  return 1
}

echo "Waiting for backend health..."
if ! wait_for_health "http://localhost:${BACKEND_PORT}/healthz"; then
  echo "Backend did not become healthy. Run ./start.sh --logs for diagnostics." >&2
  exit 1
fi

echo "Waiting for frontend health..."
if ! wait_for_health "http://localhost:${FRONTEND_PORT}/healthz"; then
  echo "Frontend did not become healthy. Run ./start.sh --logs for diagnostics." >&2
  exit 1
fi

BOOTSTRAP_TOKEN="$(sed -n 's/^BOOTSTRAP_TOKEN=//p' .env | head -n 1)"
ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"

cat <<EOF

AI-Assisted Pentest Platform is running.
  UI:       http://localhost:${FRONTEND_PORT}
  API:      http://localhost:${BACKEND_PORT}/api/v1
  API docs: http://localhost:${BACKEND_PORT}/api/docs
  Health:   http://localhost:${FRONTEND_PORT}/healthz

Services: db, s3, mock-llm, backend, worker, frontend

Initial administrator:
  1. Open the UI and use the bootstrap endpoint, or run:
     ./start.sh --bootstrap
  2. Sign in, enroll TOTP, and store the recovery codes.
  3. Create an engagement, then start a run.

Useful commands:
  ./start.sh --logs      follow logs
  ./start.sh --status    show service status
  ./start.sh --stop      stop services
  ./start.sh --reset     stop services and remove volumes

EOF

if [ "$BOOTSTRAP" -eq 1 ]; then
  if [ -z "$BOOTSTRAP_TOKEN" ]; then
    echo "BOOTSTRAP_TOKEN is not set in .env; cannot bootstrap automatically." >&2
    exit 1
  fi

  if [ -z "${ADMIN_PASSWORD:-}" ]; then
    if [ ! -t 0 ]; then
      echo "ADMIN_PASSWORD must be set when --bootstrap runs non-interactively." >&2
      exit 1
    fi
    printf 'Initial administrator username [%s]: ' "$ADMIN_USERNAME"
    read -r input_username
    ADMIN_USERNAME="${input_username:-$ADMIN_USERNAME}"
    printf 'Initial administrator password (min 12 characters): '
    stty -echo
    read -r ADMIN_PASSWORD
    stty echo
    printf '\n'
  fi

  json_escape() {
    printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
  }

  payload="$(printf '{"bootstrap_token":"%s","username":"%s","password":"%s"}' \
    "$(json_escape "$BOOTSTRAP_TOKEN")" "$(json_escape "$ADMIN_USERNAME")" "$(json_escape "$ADMIN_PASSWORD")")"

  status="$(curl -sS -o /tmp/ai-pentest-bootstrap-response.json -w '%{http_code}' \
    -X POST "http://localhost:${BACKEND_PORT}/api/v1/auth/bootstrap" \
    -H 'Content-Type: application/json' \
    -d "$payload")"

  case "$status" in
    201)
      echo "Bootstrap complete for '${ADMIN_USERNAME}'. Open http://localhost:${FRONTEND_PORT}/login."
      ;;
    409)
      echo "Bootstrap has already been completed. Sign in at http://localhost:${FRONTEND_PORT}/login."
      ;;
    *)
      echo "Bootstrap failed with HTTP ${status}:" >&2
      cat /tmp/ai-pentest-bootstrap-response.json >&2
      echo >&2
      exit 1
      ;;
  esac
  rm -f /tmp/ai-pentest-bootstrap-response.json
fi
