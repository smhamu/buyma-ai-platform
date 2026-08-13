#!/usr/bin/env bash
set -Eeuo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

env_file="${PRODUCTION_ENV_FILE:-.env.production}"
project="${COMPOSE_PROJECT_NAME:-buyma-ai-production}"
base_url="${PRODUCTION_BASE_URL:?Set PRODUCTION_BASE_URL to the ACM-backed HTTPS origin.}"

if docker compose version >/dev/null 2>&1; then
  compose=(docker compose -p "$project" --env-file "$env_file" -f docker-compose.prod.yml)
elif command -v docker-compose >/dev/null 2>&1; then
  compose=(docker-compose -p "$project" --env-file "$env_file" -f docker-compose.prod.yml)
else
  echo "Docker Compose is required." >&2
  exit 1
fi

echo "[1/8] Validating Production environment"
scripts/production/Test-ProductionEnv.sh "$env_file"
[[ "$(stat -c '%a' "$env_file")" =~ ^(600|400)$ ]] || { echo "Set $env_file permissions to 600 or 400." >&2; exit 1; }

echo "[2/8] Validating Compose"
"${compose[@]}" config --quiet

echo "[3/8] Pulling pinned runtime images and building application images"
"${compose[@]}" pull postgres redis egress_proxy
"${compose[@]}" build backend celery_worker celery_beat frontend

echo "[4/8] Starting migration dependencies"
"${compose[@]}" up -d postgres redis egress_proxy

echo "[5/8] Applying migration (deployment stops on failure)"
"${compose[@]}" run --rm backend alembic upgrade head
current="$("${compose[@]}" run --rm backend alembic current 2>/dev/null | awk '/\(head\)/ {print $1; exit}')"
head="$("${compose[@]}" run --rm backend alembic heads 2>/dev/null | awk '/\(head\)/ {print $1; exit}')"
[[ -n "$current" && "$current" == "$head" ]] || { echo "Alembic current/head mismatch." >&2; exit 1; }

echo "[6/8] Starting application"
"${compose[@]}" up -d --remove-orphans

echo "[7/8] Waiting for health checks"
services=(egress_proxy postgres redis backend frontend celery_worker celery_beat)
deadline=$((SECONDS + 180))
for service in "${services[@]}"; do
  container="$("${compose[@]}" ps -q "$service")"
  [[ -n "$container" ]] || { echo "$service container was not created." >&2; exit 1; }
  while true; do
    status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container")"
    [[ "$status" == healthy ]] && break
    [[ "$status" == unhealthy || "$status" == exited || SECONDS -ge deadline ]] && { echo "$service failed health validation: $status" >&2; exit 1; }
    sleep 3
  done
done

echo "[8/8] Running HTTPS smoke test"
scripts/production/Invoke-SmokeTest.sh "$base_url"
echo "EC2 Production deployment completed successfully."
