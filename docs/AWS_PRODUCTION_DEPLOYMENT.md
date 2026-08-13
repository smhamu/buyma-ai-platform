# AWS Production Deployment (EC2 + ALB + ACM + Route 53)

This runbook prepares a single-host MVP deployment. It does not create AWS
resources. Replace all placeholders locally and never commit `.env.production`,
administrator credentials, private keys, account IDs, or real domain names.

## Architecture

```text
Internet
  -> Route 53 alias (production hostname)
  -> Application Load Balancer
       80  -> redirect to HTTPS 443
       443 -> ACM certificate -> target group
  -> EC2 private address:FRONTEND_PORT (default/recommended 8081)
  -> frontend nginx:8080
       /api/* -> FastAPI backend:8000

Internal Docker services:
  PostgreSQL, Redis, Backend, Celery Worker, Celery Beat
  Backend/Worker -> internal egress network -> Squid -> api.openai.com:443 only
```

Only the frontend port is published on EC2. Backend 8000, PostgreSQL 5432,
Redis 6379, and Squid 3128 must never be published or permitted by an EC2
security group.

## EC2

1. Use a supported Amazon Linux or Ubuntu LTS AMI and an instance size based on
   measured Backend/Celery memory and CPU. A single EC2 host is a single point of
   failure and is suitable only for the MVP risk profile.
2. Use encrypted EBS volumes. Size and monitor both the root filesystem and Docker
   volumes. Do not use instance-store for PostgreSQL data.
3. Require IMDSv2. Attach the least-privilege IAM instance profile needed for SSM,
   monitoring, and the chosen artifact/backup location.
4. Prefer Session Manager. If SSH is retained, restrict port 22 to named management
   CIDRs and use key-based authentication only.
5. Install Docker Engine, Docker Compose, Git (or an artifact agent), `curl`, and
   `python3`. Enable Docker at boot. Do not add untrusted users to the Docker group.
6. Place the repository/artifact in a dedicated application directory owned by the
   deployment user. Set scripts executable:

   ```bash
   chmod 750 scripts/production/*.sh
   ```

Set `FRONTEND_PORT=8081` in the EC2 `.env.production`. The Compose mapping is
`${FRONTEND_PORT}:8080`, so the ALB target group uses EC2 port 8081 while nginx
continues to listen on container port 8080.

## Security groups

### ALB security group

Inbound:

- TCP 80 from `0.0.0.0/0` and `::/0`, used only for HTTPS redirect.
- TCP 443 from `0.0.0.0/0` and `::/0`.

Outbound:

- TCP 8081 to the EC2 application security group. Narrow this to the target port;
  do not use an unrestricted rule when organizational controls support SG references.

### EC2 application security group

Inbound:

- TCP 8081 from the ALB security group ID only.
- TCP 22 from explicit management CIDRs only, or omit it and use SSM.

Do not add inbound rules for 8000, 5432, 6379, or 3128. Do not allow 8081 from
the Internet. EC2 outbound must support the approved deployment/update endpoints
and OpenAI proxy traffic; use a NAT/firewall policy appropriate to the selected
public/private subnet design. Docker's Squid ACL remains a second enforcement layer.

## ALB and target group

1. Create an Application Load Balancer in at least two public subnets.
2. Create an IP or instance target group using HTTP and port 8081.
3. Configure health check path `/`, success code `200`, and a suitable interval and
   unhealthy threshold. Register the EC2 instance and wait for `healthy`.
4. Create listener 443 with the ACM certificate and a current AWS-managed TLS policy.
5. Create listener 80 with a redirect action to HTTPS, port 443, preserving host,
   path, and query.
6. Do not enable stickiness unless a measured requirement appears. Authentication
   state is token-based and does not require ALB affinity.

The frontend health check is intentionally unauthenticated. It confirms nginx can
serve the built SPA; `/api/health` is separately checked by the smoke test.

## ACM certificate and TLS

1. In the same AWS Region as the ALB, request an ACM public certificate for the
   production hostname. Add only required SANs; do not request a wildcard by default.
2. Select DNS validation. Create the ACM validation CNAME in the authoritative DNS
   zone and wait for certificate status `Issued`.
3. Attach the issued certificate to the ALB HTTPS listener and verify the expected
   hostname, chain, expiry, and automatic renewal eligibility.
4. Verify HTTP redirects to HTTPS before enabling Route 53 production traffic.

TLS terminates at ALB. nginx does not store certificates or private keys. HSTS is a
runtime opt-in and is initially disabled with an empty `HSTS_HEADER`. First verify
the ACM hostname and redirect, then ensure every in-scope subdomain supports HTTPS,
set the following exact value on EC2, and recreate only frontend:

```dotenv
HSTS_HEADER=max-age=31536000; includeSubDomains
```

```bash
docker compose -p buyma-ai-production --env-file .env.production \
  -f docker-compose.prod.yml up -d --force-recreate frontend
```

Verify the header over ALB HTTPS. Keep `HSTS_HEADER` empty for localhost and during
the initial TLS validation period.

## Route 53

1. Use the authoritative hosted zone for the production domain.
2. Create an `A` Alias record whose target is the ALB. Create an `AAAA` Alias only
   when the ALB and network design support IPv6.
3. Do not store the real domain in Compose or application source. Supply it to
   deployment and tests through `PRODUCTION_BASE_URL`/`E2E_BASE_URL`.
4. Use a temporary low DNS TTL before cutover where applicable, then verify public
   resolution from more than one network.

## Production environment and secrets

Create `.env.production` directly on EC2 through an approved secure channel. Never
copy it into an image or Git. It includes JWT secret, PostgreSQL and Redis passwords,
OpenAI key, admin bootstrap values, worker/pool settings, and `FRONTEND_PORT=8081`.

```bash
install -m 600 /dev/null .env.production
# Populate through the approved secret-transfer process without shell history.
scripts/production/Test-ProductionEnv.sh .env.production
```

Do not paste secrets into user-data, AMI build logs, CI logs, tickets, or shell
arguments. AWS Secrets Manager or encrypted SSM Parameter Store injection is a
follow-up; define IAM access, rotation, audit, and failure behavior before adoption.

### Generate `.env.production` from SSM Parameter Store

Attach an EC2 Instance Profile role; do not install `AWS_ACCESS_KEY_ID` or other
long-lived AWS credentials on the instance. Its IAM policy should allow
`ssm:GetParametersByPath` only for the regional resource path
`parameter/buyma-ai/production/*`. When SecureString parameters use a customer-managed
KMS key, also allow `kms:Decrypt` only for that key and constrain the encryption
context where possible. The AWS CLI region must be configured through EC2 deployment
configuration or `AWS_REGION`.

From the repository root:

```bash
chmod 750 scripts/production/Load-ProductionEnvFromSSM.sh
./scripts/production/Load-ProductionEnvFromSSM.sh
scripts/production/Test-ProductionEnv.sh .env.production
```

The loader calls `aws ssm get-parameters-by-path --with-decryption` only for
`/buyma-ai/production/`, maps `JWT_SECRET` to `SECRET_KEY`, URL-encodes database and
Redis passwords in connection URLs, validates a mode-600 candidate, and atomically
replaces `.env.production`. Admin bootstrap parameters are intentionally not written
to the env file. A failed retrieval, missing value, placeholder, invalid worker count,
or failed validation leaves any existing `.env.production` untouched.

## Deployment and migration

Deploy an immutable artifact or a reviewed commit. Record the prior revision/image
digests before changing the host. `Deploy-EC2.sh` deliberately does not run `git pull`
or select a branch; source acquisition belongs to the controlled release process.

Before deployment, create and move a verified backup to encrypted off-host storage.
Then run:

```bash
export PRODUCTION_ENV_FILE=.env.production
export COMPOSE_PROJECT_NAME=buyma-ai-production
export PRODUCTION_BASE_URL=https://production.example
# Optional authenticated smoke credentials should be injected, never echoed.
export SMOKE_ADMIN_EMAIL='...'
read -rsp 'Smoke password: ' SMOKE_ADMIN_PASSWORD; export SMOKE_ADMIN_PASSWORD; echo
scripts/production/Deploy-EC2.sh
unset SMOKE_ADMIN_EMAIL SMOKE_ADMIN_PASSWORD
```

The script validates file permissions and environment values, validates Compose,
pulls pinned dependencies, builds application images, starts dependencies, runs
`alembic upgrade head`, verifies `current == heads`, starts the stack, waits for all
health checks, and runs HTTPS smoke tests. `set -e` prevents application rollout when
migration fails.

## Smoke test and redirect validation

After DNS and ACM are active:

```bash
scripts/production/Invoke-SmokeTest.sh https://production.example
```

Authenticated checks use `SMOKE_ADMIN_EMAIL` and `SMOKE_ADMIN_PASSWORD`. On an
operator workstation, the existing PowerShell script also verifies redirect:

```powershell
.\scripts\production\Invoke-SmokeTest.ps1 `
  -BaseUrl https://production.example `
  -HttpUrl http://production.example
```

This covers `/`, `/login`, `/knowledge-bases`, `/api/health`, login, and the
Knowledge Base list. Do not disable TLS certificate verification.

## Playwright Production E2E

Run from a controlled runner after smoke passes:

```bash
export E2E_BASE_URL=https://production.example
export E2E_ADMIN_EMAIL='...'
export E2E_ADMIN_PASSWORD='...'
cd frontend
npm run test:e2e
```

Use the ACM certificate and normal hostname verification. Never set
`ignoreHTTPSErrors` and never run destructive E2E against irreplaceable Production
data. Confirm the existing test isolation and cleanup behavior first.

## Rollback

1. Stop and assess before rollback. Record the failed revision, logs, health state,
   migration revision, and whether any user writes occurred.
2. Application-only rollback: when database changes are backward-compatible, deploy
   the recorded previous artifact/image digests, run Compose, and repeat health and
   smoke checks. Do not automatically downgrade Alembic.
3. Migration-aware rollback: inspect the migration's documented downgrade and data
   compatibility. Prefer a forward fix for additive migrations. Run downgrade only
   after review and a fresh backup.
4. Database restore: use only for destructive/corrupting changes or an approved
   point-in-time recovery decision. Stop writers, preserve the failed database for
   forensics, validate the backup, restore to a disposable database first, and obtain
   explicit approval before replacing Production data.
5. ALB rollback: keep the target registered only when healthy. For multi-instance or
   future blue/green deployment, shift target groups after validation rather than
   mutating the live host in place.

## Backup

Take a custom-format PostgreSQL backup before deployment and validate it with
`pg_restore --list`. Store it encrypted, access-controlled, and off-host. Define and
approve retention, backup owner, schedule, RPO, and RTO. The repository's PowerShell
Backup/Restore drill remains the reference implementation; provide an equivalent
Linux automation before unattended EC2 backups are enabled.

## Firewall validation checklist

Run from a host outside the VPC, not from EC2:

- [ ] TCP 80 is reachable and redirects to HTTPS.
- [ ] TCP 443 is reachable and presents the expected ACM certificate.
- [ ] TCP 8081 is not reachable directly from the Internet.
- [ ] TCP 8000 is not reachable.
- [ ] TCP 5432 is not reachable.
- [ ] TCP 6379 is not reachable.
- [ ] TCP 3128 is not reachable.
- [ ] ALB target reports healthy on `/` port 8081.
- [ ] EC2 security group source for 8081 is the ALB SG only.

Also inspect `docker compose ps` to confirm only frontend has a published port.

## Troubleshooting

- **ALB target unhealthy:** verify EC2 SG source/port, `FRONTEND_PORT`, container
  health, target health reason, and `curl http://127.0.0.1:8081/` on EC2.
- **502 from ALB:** check frontend health and nginx logs; then Backend health and the
  internal `backend:8000` path. Do not expose Backend to diagnose it.
- **Redirect loop:** ALB listener 80 must redirect; nginx must not redirect HTTP.
  Verify ALB supplies `X-Forwarded-Proto=https` and no intermediate proxy overwrites it.
- **No HSTS:** confirm the request used public HTTPS through ALB. localhost HTTP is
  intentionally excluded.
- **OpenAI unavailable:** verify Squid health, internal proxy network, Allowed Models,
  key rotation, project quota, and that only `api.openai.com:443` is requested.
- **Migration failure:** deployment must remain stopped. Preserve logs, compare
  `alembic current` and `heads`, and choose a reviewed forward fix or rollback plan.
