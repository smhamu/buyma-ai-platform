# Production Operations

Run these commands from the repository root in PowerShell. Do not commit
`.env.production`, database dumps, administrator credentials, or smoke-test
credentials.

If the Windows execution policy blocks repository scripts, invoke them with
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File <script>`. Review the
script before using this process-scoped bypass; it does not change the machine-wide
policy.

## 1. Prepare and validate secrets

```powershell
Copy-Item .env.production.example .env.production
# Replace every placeholder and set a production-only OpenAI key.
.\scripts\production\Test-ProductionEnv.ps1
```

Generate each password and `SECRET_KEY` independently. `VITE_*` values are public
browser build inputs and must never contain credentials.

## 2. Initialize the production database

```powershell
.\scripts\production\Initialize-Production.ps1
docker compose --env-file .env.production -f docker-compose.prod.yml run --rm backend python scripts/create_admin.py
```

The initialization script validates configuration, starts PostgreSQL and Redis,
runs `alembic upgrade head`, and prints the current revision. Migration remains an
explicit deployment step and is not run concurrently by application replicas.

## 3. Start the stack

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml build
docker compose --env-file .env.production -f docker-compose.prod.yml up -d
docker compose --env-file .env.production -f docker-compose.prod.yml ps
```

Only the frontend port should be host-published. TLS termination and the public
domain must be configured before Internet exposure.

## 4. Backup and restore drill

```powershell
.\scripts\production\Backup-Postgres.ps1 -OutputDirectory D:\secure-backups
.\scripts\production\Test-Restore.ps1 -BackupFile D:\secure-backups\buyma-ai-YYYYMMDD-HHMMSS.dump
```

The restore drill creates a uniquely named disposable database, verifies its
Alembic table, and removes it afterward. Store backups encrypted and off-host.

## 5. Smoke test

Unauthenticated routing and health checks:

```powershell
.\scripts\production\Invoke-SmokeTest.ps1 -BaseUrl https://your-production-domain.example
```

Login and Knowledge Base list checks:

```powershell
$env:SMOKE_ADMIN_EMAIL = "admin@example.com"
$env:SMOKE_ADMIN_PASSWORD = Read-Host "Smoke password"
.\scripts\production\Invoke-SmokeTest.ps1 -BaseUrl https://your-production-domain.example
Remove-Item Env:SMOKE_ADMIN_EMAIL,Env:SMOKE_ADMIN_PASSWORD
```

The scripts never print secrets or tokens. Complete `MVP_RELEASE_CHECKLIST.md`
before release, including OpenAI key rotation, billing/quota alerts, HTTPS redirect,
HSTS after HTTPS validation, and Production Playwright E2E.
