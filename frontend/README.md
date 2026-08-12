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

### Docker run with Playwright official image

If Node is not installed locally, you can run Playwright from Docker:

```bash
docker run --rm -it ^
  -v "D:\SHPC_BK\Programming\buyma-ai-platform:/workspace" ^
  -w /workspace/frontend ^
  -e VITE_API_BASE_URL=http://host.docker.internal:8000 ^
  -e E2E_BASE_URL=http://127.0.0.1:5173 ^
  mcr.microsoft.com/playwright:v1.55.0-jammy ^
  sh -lc "npm ci && npx playwright test"
```

Notes:

- Keep `docker compose up -d` running for backend / postgres / redis / celery
- The Playwright config saves screenshots, traces, and videos on failure
