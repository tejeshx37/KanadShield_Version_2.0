# Setup Instructions — hand this to an AI agent (Claude Code, etc.)

Paste this whole file as your first message to the agent, in a session that
has access to this repository.

---

## Context

This is **KanadShield 2.0**, a legal & government intelligence platform.
Repo: `https://github.com/tejeshx37/KanadShield_Version_2.0`, branch
`claude/new-session-kfgl5f` (not yet merged to `main` — check with the user
whether to merge or keep working on this branch).

Read these two files first, in full, before doing anything else:

- `docs/ARCHITECTURE_AUDIT.md` — what was built, what's genuinely done vs.
  partial, and why (this environment's sandbox blocked several external
  hosts during the original build — that context matters).
- `docs/CONNECTOR_STATUS.md` — ingestion connector reachability notes.

## Non-negotiable rules to keep following

1. **No hardcoding.** Every config value (model names, endpoints,
   thresholds, weights) lives in `backend/app/core/config.py` / `.env` —
   never inline in code.
2. **No fake data, no stub modules.** If something can't be verified for
   real in this environment, say so explicitly rather than faking it.
3. **The real production database (see below) is never destructively
   modified.** No truncate, no destructive migration, no overwriting
   existing rows outside the app's own idempotent upsert logic.
4. **Every AI output must be evidence-grounded** — no summarization or
   Q&A answer that isn't traceable to retrieved document content.

## 1. Get the code

```bash
git clone https://github.com/tejeshx37/KanadShield_Version_2.0.git
cd KanadShield_Version_2.0
git checkout claude/new-session-kfgl5f
```

## 2. Connect the real database

The user has an existing PostgreSQL database with the real corpus. **Do
not point this app at a fresh empty database and re-ingest from scratch —
ask the user for the real `DATABASE_URL` first.**

```bash
cd backend
cp .env.example .env
```

Edit `.env` and set:

```
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:<port>/<real_db_name>
```

Then, **before running migrations**, inspect the real schema:

```bash
psql "$DATABASE_URL_SYNC_FORM" -c "\dt"   # or however you can connect
```

Compare it against `backend/app/models/`. If the real database's schema
differs from what this codebase expects (different column names, missing
tables, etc.), **do not force a destructive migration**. Instead:

- If the real DB is empty/fresh: run `alembic upgrade head` to create the
  schema described in `backend/alembic/versions/`.
- If the real DB already has data in a different shape: write a new,
  additive Alembic migration that reconciles the two schemas without
  dropping or truncating existing columns/tables. Ask the user before
  running anything destructive.

Required Postgres extensions (the app needs these): `vector`, `pg_trgm`,
`unaccent`. Enable them if not already present:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;
```

## 3. Redis

```bash
docker compose up -d redis
# or point REDIS_URL / CELERY_BROKER_URL / CELERY_RESULT_BACKEND at an
# existing Redis instance in .env
```

## 4. LLM / embedding provider

Default is fully local (no API keys needed):

- **Ollama** for the LLM — install from https://ollama.com, then
  `ollama pull llama3.1` (or whatever `OLLAMA_LLM_MODEL` is set to), and
  make sure `OLLAMA_BASE_URL` in `.env` points at it.
- **`BAAI/bge-m3`** for embeddings — downloads automatically from Hugging
  Face on first use (needs outbound network access to `huggingface.co`;
  this was blocked in the original build sandbox, so this was never
  live-verified there — verify it here).

To use a commercial/self-hosted OpenAI-compatible endpoint instead, set in
`.env`:

```
AI_PROVIDER=openai_compatible
OPENAI_COMPATIBLE_BASE_URL=...
OPENAI_COMPATIBLE_API_KEY=...
OPENAI_COMPATIBLE_LLM_MODEL=...
```

## 5. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head        # only after step 2's schema check
uvicorn app.main:app --reload
```

Verify: `curl http://localhost:8000/health` → `{"status":"ok"}`.

Run tests (creates/uses a separate `<dbname>_test` database, never the
real one):

```bash
pytest
```

## 6. Celery workers

Ingestion, alert evaluation, and AI summarize/ask jobs all run here —
without this running, `/api/v1/ai/*` endpoints will enqueue jobs that
never complete.

```bash
cd backend && source .venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info
```

## 7. Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_BASE_URL` in a `frontend/.env` if the backend isn't at
`/api/v1` on the same host (Vite dev server proxies `/api` to
`VITE_API_PROXY_TARGET`, default `http://localhost:8000`).

Run tests: `npm run test`. Build: `npm run build`.

## 8. First real ingestion run

Once the DB/Redis/Ollama/backend/Celery are all up, trigger a connector
manually to prove the pipeline works against live data (the connectors
were never live-tested in the original build sandbox):

```python
from app.workers.ingestion_tasks import run_ingestion_for_source
run_ingestion_for_source.delay("SOURCE_GUJARAT_GR")
```

Check `ingestion_runs` and `ingestion_dead_letters` tables afterward. If a
connector's HTML selectors don't match the live site anymore, fix the
selectors in `backend/app/services/ingestion/connectors/` — the pipeline
architecture doesn't need to change, only that one connector.

## 9. What to verify first

Given several things were never live-verified in the original build
sandbox (documented in `docs/ARCHITECTURE_AUDIT.md`), prioritize checking:

1. Real ingestion from at least one connector end-to-end.
2. Real semantic search (`BAAI/bge-m3` embeddings) returning sensible
   cross-language results (there's a real test for this,
   `backend/tests/test_cross_language_embeddings.py`, that was skipped —
   run it here; it should now pass).
3. A real Ollama-backed `/api/v1/ai/summarize/{id}` and `/api/v1/ai/ask`
   call against real ingested content.
4. The full golden path in the browser: search → filter → document → AI
   summary → related act → related judgment → graph → timeline → schemes.
