# KanadShield 2.0

Unified legal & government intelligence platform — Acts, Rules, Gazettes,
Government Resolutions, notifications, and court judgments, cross-referenced,
searchable, and grounded in the original source.

See [`docs/ARCHITECTURE_AUDIT.md`](docs/ARCHITECTURE_AUDIT.md) for the
backend's full build audit and honest done/partial/not-done status per
module. See [`docs/CONNECTOR_STATUS.md`](docs/CONNECTOR_STATUS.md) for
ingestion connector reachability notes, and
[`docs/API_CONTRACT.md`](docs/API_CONTRACT.md) for how the frontend was
reconciled against the real backend routes (including the notable gaps it
had to work around).

## Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.x (async), Alembic, Pydantic v2, Celery
- **Database**: PostgreSQL + pgvector + PostgreSQL full-text search
- **Cache/Jobs**: Redis + Celery
- **Frontend**: React + TypeScript + Vite + Tailwind v4 + TanStack Query + Zustand + React Router
- **AI**: Ollama (LLM) + sentence-transformers (`BAAI/bge-m3`) + PyMuPDF + Tesseract OCR + faster-whisper — all local by default; commercial providers are an optional config swap, never required

## Local setup

### 1. Infrastructure

```bash
docker compose up -d postgres redis
# Ollama is optional — omit it and set AI_PROVIDER=openai_compatible if you
# prefer a commercial/self-hosted LLM endpoint instead.
docker compose up -d ollama
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit as needed
alembic upgrade head
uvicorn app.main:app --reload
```

Run tests: `pytest`

### 3. Celery workers (ingestion, alerts, AI jobs)

```bash
cd backend && source .venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info
```

### 4. Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

`VITE_API_BASE_URL` in `.env` should point at the backend started in step 2.
Build: `npm run build`.

## Frontend status

The frontend implements the canonical navy/gold/parchment design system from
the frontend implementation spec, with routing matching its information
architecture:

- Design token system, sidebar/canvas layout, language/department switchers (`frontend/src/`)
- Dashboard, Research (search + filters), Archives (list + document detail
  with cross-links, knowledge graph, and on-demand AI summary) — wired to
  the real backend's actual routes and response shapes
- Insights, Public Service (DigiLocker), Library, Support — routed but
  explicitly marked "not yet implemented," per the spec's Definition of
  Done (no fake-data screens)

Its API layer was originally written against a self-authored contract
before the real backend existed in this branch; it has since been
reconciled to call the actual FastAPI routes and shapes — see
[`docs/API_CONTRACT.md`](docs/API_CONTRACT.md) for what changed and the
handful of real backend gaps (no document status field, no document→graph
lookup route) that required a small, justified backend addition or an
honest client-side workaround rather than invented data.

## Configuration

Every environment-dependent value (model names, endpoints, weights,
thresholds, feature flags) lives in `backend/.env` / `backend/app/core/config.py`
— see `backend/.env.example` for the full list. Nothing is hardcoded in
application code.

## Repository layout

```
backend/app/{api,core,db,models,repositories,schemas,services,intelligence,search,workers,utils}/
frontend/src/{api,components,pages,store,i18n,lib}/
docs/
```
