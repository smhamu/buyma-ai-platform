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
```

### Notes

- `VITE_API_BASE_URL` should point to the local backend API base URL
- `.env.development` is for local development values and is excluded from git
- Do not put secrets into frontend environment variables unless they are safe to expose to the browser
