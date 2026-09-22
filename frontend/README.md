# Cenidim Web – Frontend

Vue 3 + TypeScript SPA for the Cenidim Web Application, built with
**Vite**. It talks to the FastAPI backend at `/api` and is served by an
unprivileged Nginx container (see `frontend/Dockerfile`).

## Features

- **Catálogo (Canciones)**: search across titles, albums and lyrics
  with free-text + classification filters, "Solo con letra", sortable
  columns, and a pagination bar (20 / 50 / 100 per page).
- **Dashboard**: KPIs, timelines and charts (vue-chartjs), plus a
  responsive word cloud rendered as frequency-scaled chips.
- **Panel de Administración**: role-gated (viewer / editor / admin)
  CRUD over fonogramas, canciones and usuarios, with server-side
  sorting and shared pagination.
- **Auth**: JWT with HttpOnly cookies, password reset via email, and
  role-based access control.

## Requirements

- **Node.js 24** (the version pinned in CI via `actions/setup-node`).

## Available Scripts

Run from `frontend/`:

| Command | What it does |
|---------|--------------|
| `npm install` / `npm ci` | Install dependencies |
| `npm run dev` | Vite dev server on `:5173`, proxies `/api` to the backend |
| `npm run build` | TypeScript check (`vue-tsc --noEmit`) + production build |
| `npx vue-tsc --noEmit` | Standalone typecheck (no dedicated npm script) |
| `npm run lint` / `lint:fix` | ESLint |
| `npm run test` | Vitest watch mode |
| `npm run test -- --run` | One-shot test run (CI) |
| `npm run test:coverage` | Coverage report |
| `npm run test:e2e` | Playwright end-to-end tests (needs the stack running) |

### Known issue: `localStorage` under Node ≥ 22

Recent Node versions ship a built-in `localStorage` global that
shadows jsdom's and makes ~63 tests fail with
`Cannot read properties of undefined (reading 'clear')`. Workaround
until the test setup is patched:

```bash
NODE_OPTIONS="--localstorage-file=/tmp/ls" npm run test -- --run
```

## Docker

The frontend is built with **Vite** (not react-scripts) and served from
`frontend/Dockerfile` using `nginx-unprivileged:alpine` (non-root, port
80). The production bundle is emitted to `frontend/dist/` and committed
so the committed artifact matches what the Nginx image serves.

For full-stack orchestration, use the root `docker-compose.yaml` (or
`docker-compose-coolify.yaml` for the Coolify deployment).
