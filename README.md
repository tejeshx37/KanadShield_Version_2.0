# KanadShield 2.0

Unified legal & government intelligence platform — Acts, Rules, Gazettes,
Government Resolutions, notifications, and court judgments, cross-referenced,
searchable, and grounded in the original source.

See [`docs/ARCHITECTURE_AUDIT.md`](docs/ARCHITECTURE_AUDIT.md) for the full
build audit, adaptations made in this environment, and honest
done/partial/not-done status per module. See
[`docs/CONNECTOR_STATUS.md`](docs/CONNECTOR_STATUS.md) for ingestion
connector reachability notes.

## Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.x (async), Alembic, Pydantic v2, Celery
- **Database**: PostgreSQL + pgvector + PostgreSQL full-text search
- **Cache/Jobs**: Redis + Celery
- **Frontend**: React + TypeScript + Vite + Tailwind + TanStack Query + Zustand, PWA
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
npm install
npm run dev
```

Run tests: `npm run test`. Build: `npm run build`.

## Configuration

Every environment-dependent value (model names, endpoints, weights,
thresholds, feature flags) lives in `backend/.env` / `backend/app/core/config.py`
— see `.env.example` for the full list. Nothing is hardcoded in application code.

## Repository layout

```
backend/app/{api,core,db,models,repositories,schemas,services,intelligence,search,workers,utils}/
frontend/src/{api,components,features,pages,lib,store}/
docs/
```
