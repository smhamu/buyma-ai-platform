#!/usr/bin/env bash
set -euo pipefail

env_file="${1:-.env.production}"
[[ -f "$env_file" ]] || { echo "Production environment file not found." >&2; exit 1; }

declare -A values=()
while IFS= read -r line || [[ -n "$line" ]]; do
  [[ "$line" =~ ^[[:space:]]*# || "$line" != *=* ]] && continue
  key="${line%%=*}"
  value="${line#*=}"
  key="${key//[[:space:]]/}"
  values["$key"]="$value"
done < "$env_file"

errors=0
required=(APP_ENV POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD DATABASE_URL REDIS_PASSWORD CELERY_BROKER_URL CELERY_RESULT_BACKEND SECRET_KEY OPENAI_API_KEY)
for key in "${required[@]}"; do
  value="${values[$key]:-}"
  if [[ -z "$value" ]]; then
    echo "ERROR: $key is missing or empty." >&2
    errors=1
  elif [[ "$value" == *CHANGE_ME* ]]; then
    echo "ERROR: $key still contains a placeholder." >&2
    errors=1
  fi
done

[[ "${values[APP_ENV]:-}" == production ]] || { echo "ERROR: APP_ENV must be production." >&2; errors=1; }
[[ "${values[DATABASE_ECHO]:-}" == false ]] || { echo "ERROR: DATABASE_ECHO must be false." >&2; errors=1; }
[[ "${values[REGISTRATION_ENABLED]:-}" == false ]] || { echo "ERROR: REGISTRATION_ENABLED must be false." >&2; errors=1; }
[[ "${values[ENABLE_API_DOCS]:-}" == false ]] || { echo "ERROR: ENABLE_API_DOCS must be false." >&2; errors=1; }
hsts_header="${values[HSTS_HEADER]:-}"
[[ -z "$hsts_header" || "$hsts_header" == "max-age=31536000; includeSubDomains" ]] || { echo "ERROR: HSTS_HEADER is not an approved value." >&2; errors=1; }
secret_key="${values[SECRET_KEY]:-}"
(( ${#secret_key} >= 32 )) || { echo "ERROR: SECRET_KEY must be at least 32 characters." >&2; errors=1; }
notification_provider="${values[NOTIFICATION_DELIVERY_PROVIDER]:-disabled}"
case "$notification_provider" in
  disabled) ;;
  slack)
    [[ -n "${values[SLACK_WEBHOOK_URL]:-}" ]] || { echo "ERROR: SLACK_WEBHOOK_URL is required for Slack delivery." >&2; errors=1; }
    ;;
  noop)
    echo "ERROR: noop notification delivery is prohibited in production." >&2
    errors=1
    ;;
  *)
    echo "ERROR: NOTIFICATION_DELIVERY_PROVIDER is invalid." >&2
    errors=1
    ;;
esac
[[ "${values[NOTIFICATION_SECRET_STORE]:-ssm}" == ssm ]] || { echo "ERROR: Production notification secrets must use SSM." >&2; errors=1; }

(( errors == 0 )) || { echo "Production environment validation failed. Secret values were not printed." >&2; exit 1; }
echo "Production environment validation passed. Secret values were not printed."
