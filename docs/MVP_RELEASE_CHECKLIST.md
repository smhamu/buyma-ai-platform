# MVP Release Checklist

Do not expose the service to the Internet until every P0 item is complete.

## Deployment configuration

- [x] Copy `.env.production.example` to `.env.production` outside source control.
- [x] Replace every `CHANGE_ME` value with independently generated secrets.
- [x] Confirm `APP_ENV=production`, `DATABASE_ECHO=false`, `REGISTRATION_ENABLED=false`, and `ENABLE_API_DOCS=false`.
- [ ] Confirm only the TLS reverse proxy/frontend port is Internet-accessible.
- [x] Confirm PostgreSQL, Redis, and FastAPI have no host-published ports.
- [ ] Configure TLS termination, HTTP-to-HTTPS redirect, and the production domain.
- [ ] Add HSTS only after HTTPS works on the production domain and all subdomains in scope.
- [x] Run `scripts/production/Test-ProductionEnv.ps1` without errors.

## AWS EC2 / ALB / ACM / Route 53

- [ ] Provision EC2 with encrypted EBS, IMDSv2, least-privilege IAM, and SSM access.
- [ ] Set EC2 `.env.production` permissions to 600 and validate it without printing secrets.
- [ ] Restrict EC2 frontend port 8081 inbound to the ALB security group only.
- [ ] Confirm EC2 has no Internet inbound access to 8081, 8000, 5432, 6379, or 3128.
- [ ] Configure ALB target group HTTP:8081 health check `/` and confirm healthy.
- [ ] Issue and DNS-validate the production hostname certificate in regional ACM.
- [ ] Configure ALB HTTPS 443 with ACM and HTTP 80 to HTTPS redirect.
- [ ] Create Route 53 Alias record from the production hostname to the ALB.
- [ ] Verify the public ACM certificate and HTTP-to-HTTPS redirect externally.
- [ ] Verify HSTS is present over ALB HTTPS and absent on direct localhost HTTP.
- [ ] Run `Deploy-EC2.sh` successfully against the reviewed release artifact.
- [ ] Run authenticated HTTPS smoke and Production Playwright E2E against the production hostname.
- [ ] Verify externally that only ports 80/443 are reachable.

## Database and identity

- [x] Provision a new production database; do not clone development test data.
- [x] Run `docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head` as a deployment step.
- [x] Verify `docker compose -f docker-compose.prod.yml run --rm backend alembic current` reports the expected head.
- [x] Create the initial administrator without exposing its password in command arguments or logs.
- [x] Confirm no `tx-*`, `kb-stats-e2e-*`, or `e2e-*` users/resources exist.

## Backup and restore drill

- [ ] Create an encrypted, access-controlled backup location outside the application host.
- [x] Create a custom-format Production dump without passing binary data through a PowerShell pipeline, and validate it with `pg_restore --list`.
- [x] Restore into a disposable database and verify Alembic head, required tables, active Admin presence, and row counts.
- [x] Confirm the restore database and container-side temporary dump are removed after the drill.
- [ ] Record backup retention, owner, schedule, recovery point objective, and recovery time objective.
- [x] Run `Backup-Postgres.ps1` and `Test-Restore.ps1` against the production-like environment.

## Runtime health and cost controls

- [x] Frontend, Backend, PostgreSQL, Redis, and Celery Worker are healthy.
- [x] Celery Beat is running exactly once.
- [x] OpenAI Production Project spend limit, 50/80/100% alerts, and allowed-model restrictions are configured.
- [x] Restrict Production Backend and Celery Worker egress through a no-log allowlist proxy for `api.openai.com:443` only.
- [x] Verify the current Production OpenAI API key authenticates through the allowlist proxy.
- [x] Verify Production TXT ingestion reaches Ready and RAG returns sources through the OpenAI allowlist proxy.
- [ ] Confirm nginx rate limiting returns HTTP 429 under sustained abuse.
- [ ] Review application, nginx, and Celery logs without Authorization headers or secrets.

## Release verification

- [x] Production-like localhost smoke test passes for `/`, `/login`, `/api/health`, login, and the Knowledge Base list.

- [ ] Backend: `pytest -m "not evaluation"`.
- [ ] Frontend: build, lint, typecheck, and unit tests.
- [ ] Production Playwright E2E passes.
- [ ] Login, Knowledge Base list/detail, upload, versioning, diff, restore, and logout smoke tests pass over HTTPS.
- [ ] IDOR direct-access test returns Not Found.
- [ ] A rollback image and database restore procedure are documented and available.
- [ ] Run `Invoke-SmokeTest.ps1` against the HTTPS production domain.

## Token storage risk acceptance

The MVP stores access and refresh tokens in `sessionStorage`. This limits persistence
to the browser tab but does not protect tokens from successful same-origin XSS.
Moving refresh tokens to `HttpOnly`, `Secure`, `SameSite` cookies requires an auth
contract change plus CSRF protection and is tracked as a P1 follow-up. Until then,
keep the CSP/security-header review, dependency patching, and XSS regression checks
in the release process.
