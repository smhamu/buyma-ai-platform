#!/usr/bin/env bash
set -euo pipefail

base_url="${1:-https://example.invalid}"
base_url="${base_url%/}"

for path in / /login /knowledge-bases /api/health; do
  status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' "${base_url}${path}")"
  [[ "$status" == 200 ]] || { echo "${path} returned HTTP ${status}." >&2; exit 1; }
  echo "PASS GET ${path} -> 200"
done

if [[ -z "${SMOKE_ADMIN_EMAIL:-}" || -z "${SMOKE_ADMIN_PASSWORD:-}" ]]; then
  echo "Authentication smoke test skipped. Set SMOKE_ADMIN_EMAIL and SMOKE_ADMIN_PASSWORD to enable it."
  exit 0
fi

login_body="$(SMOKE_ADMIN_EMAIL="$SMOKE_ADMIN_EMAIL" SMOKE_ADMIN_PASSWORD="$SMOKE_ADMIN_PASSWORD" python3 - <<'PY'
import json, os
print(json.dumps({"email": os.environ["SMOKE_ADMIN_EMAIL"], "password": os.environ["SMOKE_ADMIN_PASSWORD"]}))
PY
)"
login_response="$(curl --silent --show-error --fail-with-body -H 'Content-Type: application/json' --data "$login_body" "${base_url}/api/auth/login")"
token="$(LOGIN_RESPONSE="$login_response" python3 - <<'PY'
import json, os
print(json.loads(os.environ["LOGIN_RESPONSE"])["data"]["access_token"])
PY
)"
[[ -n "$token" ]] || { echo "Login response did not contain an access token." >&2; exit 1; }

kb_response="$(curl --silent --show-error --fail-with-body -H "Authorization: Bearer ${token}" "${base_url}/api/knowledge-bases")"
KB_RESPONSE="$kb_response" python3 - <<'PY'
import json, os
assert json.loads(os.environ["KB_RESPONSE"])["success"] is True
PY
echo "PASS POST /api/auth/login"
echo "PASS GET /api/knowledge-bases"
echo "Smoke test completed. Credentials and tokens were not printed."
