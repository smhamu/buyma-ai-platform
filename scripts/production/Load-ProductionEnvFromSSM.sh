#!/usr/bin/env bash
set -euo pipefail

# This script intentionally relies on the EC2 Instance Profile credential chain.
# Do not supply or persist static AWS access keys on the host.

readonly parameter_path="/buyma-ai/production/"
readonly script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly repo_root="$(cd "$script_dir/../.." && pwd)"
readonly template_file="$repo_root/.env.production.example"
readonly output_file="$repo_root/.env.production"
readonly validator="$script_dir/Test-ProductionEnv.sh"

response_file=""
aws_error_file=""
generated_file=""
validation_log=""

cleanup() {
  if [[ -n "$response_file" ]]; then rm -f -- "$response_file"; fi
  if [[ -n "$aws_error_file" ]]; then rm -f -- "$aws_error_file"; fi
  if [[ -n "$generated_file" ]]; then rm -f -- "$generated_file"; fi
  if [[ -n "$validation_log" ]]; then rm -f -- "$validation_log"; fi
  return 0
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

fail() {
  echo "Production environment generation failed${1:+ during $1}. Secret values were not printed." >&2
  exit 1
}

command -v aws >/dev/null 2>&1 || { echo "AWS CLI is required." >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "python3 is required." >&2; exit 1; }
[[ -f "$template_file" && -f "$validator" ]] || fail "prerequisite validation"

response_file="$(mktemp "$repo_root/.ssm-production-response.XXXXXX")" || fail "temporary file creation"
aws_error_file="$(mktemp "$repo_root/.ssm-production-error.XXXXXX")" || fail "temporary file creation"
generated_file="$(mktemp "$repo_root/.env.production.tmp.XXXXXX")" || fail "temporary file creation"
chmod 600 "$response_file" "$aws_error_file" "$generated_file" || fail "temporary file protection"

# AWS CLI automatically follows NextToken unless --no-paginate is supplied.
# Stdout and stderr are captured in mode-600 files and never replayed.
if ! AWS_PAGER="" aws ssm get-parameters-by-path \
  --path "$parameter_path" \
  --recursive \
  --with-decryption \
  --output json \
  >"$response_file" 2>"$aws_error_file"; then
  fail "SSM retrieval"
fi

if ! python3 - "$response_file" "$template_file" "$generated_file" "$parameter_path" <<'PY'
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

response_path, template_path, generated_path, parameter_path = sys.argv[1:]
required = {
    "SECRET_KEY",
    "OPENAI_API_KEY",
    "POSTGRES_PASSWORD",
    "REDIS_PASSWORD",
    "UVICORN_WORKERS",
}


def abort() -> None:
    raise SystemExit(1)


def dotenv_quote(value: str) -> str:
    # Compose dotenv single quotes prevent interpolation of $, #, and backslashes.
    # Compose accepts backslash-escaped single quotes inside single-quoted values.
    if any(character in value for character in ("\x00", "\r", "\n")):
        abort()
    return "'" + value.replace("'", "\\'") + "'"


try:
    payload = json.loads(Path(response_path).read_text(encoding="utf-8"))
    parameters = payload.get("Parameters")
    if not isinstance(parameters, list):
        abort()

    values: dict[str, str] = {}
    for parameter in parameters:
        if not isinstance(parameter, dict):
            abort()
        name = parameter.get("Name")
        value = parameter.get("Value")
        if not isinstance(name, str) or not name.startswith(parameter_path):
            abort()
        short_name = name[len(parameter_path):]
        # Reject nested/unexpected path shapes and duplicate names. ADMIN_* values
        # may be returned but are deliberately ignored and never written.
        if not short_name or "/" in short_name or short_name in values:
            abort()
        if not isinstance(value, str):
            abort()
        values[short_name] = value

    if not required.issubset(values):
        abort()
    if any(not values[key] for key in required):
        abort()
    if any("CHANGE_ME" in values[key] for key in required):
        abort()
    if not re.fullmatch(r"[1-9][0-9]*", values["UVICORN_WORKERS"]):
        abort()
    if len(values["SECRET_KEY"]) < 32:
        abort()

    template = Path(template_path).read_text(encoding="utf-8")
    lines = template.splitlines()
    template_values: dict[str, str] = {}
    key_indexes: dict[str, int] = {}
    for index, line in enumerate(lines):
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in key_indexes:
            abort()
        key_indexes[key] = index
        template_values[key] = value

    needed_template_keys = {
        "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "DATABASE_URL",
        "REDIS_PASSWORD", "CELERY_BROKER_URL", "CELERY_RESULT_BACKEND",
        "SECRET_KEY", "OPENAI_API_KEY", "UVICORN_WORKERS",
    }
    if not needed_template_keys.issubset(key_indexes):
        abort()

    postgres_user = template_values["POSTGRES_USER"]
    postgres_db = template_values["POSTGRES_DB"]
    if not postgres_user or not postgres_db or "CHANGE_ME" in postgres_user or "CHANGE_ME" in postgres_db:
        abort()

    postgres_password = values["POSTGRES_PASSWORD"]
    redis_password = values["REDIS_PASSWORD"]
    postgres_url_password = quote(postgres_password, safe="")
    redis_url_password = quote(redis_password, safe="")

    replacements = {
        "UVICORN_WORKERS": values["UVICORN_WORKERS"],
        "POSTGRES_PASSWORD": dotenv_quote(postgres_password),
        "DATABASE_URL": dotenv_quote(
            f"postgresql+asyncpg://{quote(postgres_user, safe='')}:{postgres_url_password}"
            f"@postgres:5432/{quote(postgres_db, safe='')}"
        ),
        "REDIS_PASSWORD": dotenv_quote(redis_password),
        "CELERY_BROKER_URL": dotenv_quote(f"redis://:{redis_url_password}@redis:6379/0"),
        "CELERY_RESULT_BACKEND": dotenv_quote(f"redis://:{redis_url_password}@redis:6379/1"),
        "SECRET_KEY": dotenv_quote(values["SECRET_KEY"]),
        "OPENAI_API_KEY": dotenv_quote(values["OPENAI_API_KEY"]),
    }
    # Slack is optional while delivery is disabled. If provisioned in SSM, keep
    # it secret and map it without ever printing the value.
    if "SLACK_WEBHOOK_URL" in values:
        if not values["SLACK_WEBHOOK_URL"] or "SLACK_WEBHOOK_URL" not in key_indexes:
            abort()
        replacements["SLACK_WEBHOOK_URL"] = dotenv_quote(values["SLACK_WEBHOOK_URL"])

    for key, value in replacements.items():
        lines[key_indexes[key]] = f"{key}={value}"

    generated = "\n".join(lines) + "\n"
    for line in generated.splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        _, value = line.split("=", 1)
        if "CHANGE_ME" in value:
            abort()

    Path(generated_path).write_text(generated, encoding="utf-8")
except (OSError, ValueError, TypeError, json.JSONDecodeError):
    abort()
PY
then
  fail "candidate generation"
fi

chmod 600 "$generated_file" || fail "candidate protection"
[[ -s "$generated_file" ]] || fail "candidate generation"

# Validate the candidate before touching an existing Production file.
validation_log="$(mktemp "$repo_root/.production-validation.XXXXXX")" || fail "temporary file creation"
chmod 600 "$validation_log" || fail "temporary file protection"
if ! bash "$validator" "$generated_file" >"$validation_log" 2>&1; then
  rm -f -- "$validation_log"
  validation_log=""
  fail "candidate validation"
fi
rm -f -- "$validation_log"
validation_log=""

# The temporary file is on the same filesystem as the destination, so rename is atomic.
mv -f -- "$generated_file" "$output_file" || fail "atomic replacement"
generated_file=""
chmod 600 "$output_file" || fail "output protection"

echo "Production environment file generated successfully."
echo "Path: .env.production"
echo "Permissions: 600"
