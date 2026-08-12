# MVP Release Checklist

Do not expose the service to the Internet until every P0 item is complete.

## Deployment configuration

- [ ] Copy `.env.production.example` to `.env.production` outside source control.
- [ ] Replace every `CHANGE_ME` value with independently generated secrets.
- [ ] Confirm `APP_ENV=production`, `DATABASE_ECHO=false`, `REGISTRATION_ENABLED=false`, and `ENABLE_API_DOCS=false`.
- [ ] Confirm only the TLS reverse proxy/frontend port is Internet-accessible.
- [ ] Confirm PostgreSQL, Redis, and FastAPI have no host-published ports.
- [ ] Configure TLS termination, HTTP-to-HTTPS redirect, and the production domain.
- [ ] Add HSTS only after HTTPS works on the production domain and all subdomains in scope.

## Database and identity

- [ ] Provision a new production database; do not clone development test data.
- [ ] Run `docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head` as a deployment step.
- [ ] Verify `docker compose -f docker-compose.prod.yml run --rm backend alembic current` reports the expected head.
- [ ] Create the initial administrator interactively with `docker compose -f docker-compose.prod.yml run --rm backend python scripts/create_admin.py`.
- [ ] Confirm no `tx-*`, `kb-stats-e2e-*`, or `e2e-*` users/resources exist.

## Backup and restore drill

- [ ] Create an encrypted, access-controlled backup location outside the application host.
- [ ] Run `docker compose -f docker-compose.prod.yml exec -T postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > buyma-ai.dump`.
- [ ] Restore into a disposable database and verify it: `pg_restore --clean --if-exists --no-owner --dbname=<restore-db> buyma-ai.dump`.
- [ ] Record backup retention, owner, schedule, recovery point objective, and recovery time objective.

## Runtime health and cost controls

- [ ] Frontend, Backend, PostgreSQL, Redis, and Celery Worker are healthy.
- [ ] Celery Beat is running exactly once.
- [ ] OpenAI billing limit, project quota, and provider alerts are configured.
- [ ] Confirm nginx rate limiting returns HTTP 429 under sustained abuse.
- [ ] Review application, nginx, and Celery logs without Authorization headers or secrets.

## Release verification

- [ ] Backend: `pytest -m "not evaluation"`.
- [ ] Frontend: build, lint, typecheck, and unit tests.
- [ ] Production Playwright E2E passes.
- [ ] Login, Knowledge Base list/detail, upload, versioning, diff, restore, and logout smoke tests pass over HTTPS.
- [ ] IDOR direct-access test returns Not Found.
- [ ] A rollback image and database restore procedure are documented and available.

## Token storage risk acceptance

The MVP stores access and refresh tokens in `sessionStorage`. This limits persistence
to the browser tab but does not protect tokens from successful same-origin XSS.
Moving refresh tokens to `HttpOnly`, `Secure`, `SameSite` cookies requires an auth
contract change plus CSRF protection and is tracked as a P1 follow-up. Until then,
keep the CSP/security-header review, dependency patching, and XSS regression checks
in the release process.
