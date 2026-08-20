# KanadShield_Version_2.0

Unified Legal & Government Intelligence Platform.

## Frontend

The frontend lives in `frontend/` (React + TypeScript + Vite, Tailwind v4,
TanStack Query, Zustand, React Router). See `frontend/README.md` (Vite
default) for local dev commands:

```
cd frontend
cp .env.example .env
npm install
npm run dev
```

`VITE_API_BASE_URL` in `.env` must point at a running backend implementing
the contract documented in [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md).
No backend exists in this repository yet, so API calls will fail until one
is built or pointed at.

### What's implemented

- Design token system, sidebar/canvas layout, routing, language/department
  switchers (`frontend/src/`)
- Dashboard, Research (search + filters), Archives (list + document detail
  with cross-links and knowledge graph) — fully wired to real query hooks
  against the documented API contract
- Insights, Public Service (DigiLocker), Library, Support — routed but
  explicitly marked "not yet implemented," per the frontend spec's
  Definition of Done (no fake data screens)
