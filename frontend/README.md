# BUYMA AI Platform Frontend

## Local development

This frontend uses Vite.
For local development, Vite automatically loads `frontend/.env.development`.

### Environment variables

Create `frontend/.env.development` from `frontend/.env.example`.

Example:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### Install dependencies

```bash
npm install
```

### Start development server

```bash
npm run dev
```

The app will start with the values from `frontend/.env.development`.

### Available scripts

```bash
npm run dev
npm run build
npm run lint
npm run typecheck
npm run test
npm run test:e2e
npm run test:e2e:ui
```

### Notes

- `VITE_API_BASE_URL` should point to the local backend API base URL
- `.env.development` is for local development values and is excluded from git
- Do not put secrets into frontend environment variables unless they are safe to expose to the browser

## Playwright E2E

### E2E environment variables

Add these keys when you want to override the default E2E setup:

```env
E2E_BASE_URL=http://127.0.0.1:5173
E2E_ADMIN_EMAIL=
E2E_ADMIN_PASSWORD=
E2E_USER_EMAIL=
E2E_USER_PASSWORD=
```

- If `E2E_ADMIN_EMAIL` / `E2E_ADMIN_PASSWORD` are not set, the E2E suite creates a temporary primary user with the existing register API
- If `E2E_USER_EMAIL` / `E2E_USER_PASSWORD` are not set, the IDOR check creates a temporary second user

### Local run

Start backend services first:

```bash
docker compose up -d
```

Then run:

```bash
npm run test:e2e
```

Run only the luxury research flow (admin credentials are required):

```bash
npx playwright test e2e/luxury-research.spec.ts
```

The spec creates uniquely named Brand, Supplier, and Candidate records and
removes them in Candidate → Supplier → Brand order even when the test fails.

### Docker run with Playwright official image

If Node is not installed locally, you can run Playwright from Docker:

```bash
docker run --rm -it ^
  -v "D:\SHPC_BK\Programming\buyma-ai-platform:/workspace" ^
  -w /workspace/frontend ^
  -e VITE_API_BASE_URL=http://host.docker.internal:8000 ^
  -e E2E_BASE_URL=http://127.0.0.1:5173 ^
  mcr.microsoft.com/playwright:v1.55.1-jammy ^
  sh -lc "npm ci && npx playwright test"
```

Notes:

- Keep `docker compose up -d` running for backend / postgres / redis / celery
- The Playwright config saves screenshots, traces, and videos on failure

## Production-like deployment

The production image uses a Node 20 multi-stage build and serves the generated
Vite bundle from nginx. The browser calls `/api/*` on the same origin. nginx
removes the `/api` prefix and proxies the request to `backend:8000`.

`VITE_API_BASE_URL` is a Vite build-time value, not a container runtime setting.
The Docker build defaults it to `/api`. To build with a different public API base,
pass a build argument explicitly; do not expect an environment variable added to
an already-built frontend container to change the bundle.

Build and start the production-like frontend with the existing backend stack:

```bash
docker compose build frontend
docker compose up -d frontend
```

Open:

```text
http://localhost:8080
```

The nginx SPA fallback supports direct access and reloads for routes such as:

```text
/login
/knowledge-bases
/knowledge-bases/:id
/knowledge-bases/:id/documents
/knowledge-bases/:id/documents/:documentId
```

Development continues to use Vite and `frontend/.env.development`:

```bash
npm run dev
```

### E2E against the production frontend

Keep the Compose stack, including `frontend`, running and point Playwright at
port 8080. `VITE_API_BASE_URL` below is used by E2E setup and cleanup requests;
the browser application itself uses the nginx `/api` proxy baked into the image.

PowerShell:

```powershell
$env:E2E_BASE_URL = "http://localhost:8080"
$env:VITE_API_BASE_URL = "http://localhost:8000"
npm run test:e2e
```

Docker-based Playwright execution:

```powershell
docker run --rm --add-host=host.docker.internal:host-gateway `
  -v "${PWD}/frontend:/work" `
  -w /work `
  -e E2E_BASE_URL=http://host.docker.internal:8080 `
  -e VITE_API_BASE_URL=http://host.docker.internal:8000 `
  mcr.microsoft.com/playwright:v1.55.1-jammy `
  npm run test:e2e
```

## MVP release hardening

Production deployment uses `docker-compose.prod.yml`, not the development Compose
file. It publishes only the frontend port; Backend, PostgreSQL, and Redis remain on
internal Docker networks. Complete [the release checklist](../docs/MVP_RELEASE_CHECKLIST.md)
before exposing the application to the Internet. See the
[production operations guide](../docs/PRODUCTION_OPERATIONS.md) for environment
validation, database initialization, backup/restore, and smoke-test commands.
