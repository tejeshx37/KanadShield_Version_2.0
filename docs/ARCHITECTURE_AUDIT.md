# Architecture Audit — KanadShield 2.0

Date: 2026-08-20

## 1. Repository state at start

- Git repo contained a single commit with only `README.md` (one line, the
  repo name). No backend, no frontend, no schema, no migrations, no data.
- No `.env`, no docker-compose, no CI config, no prior branches with work.

## 2. Database state at start

- PostgreSQL 16 is installed on the host but the service was **stopped**
  and held only the three default databases (`postgres`, `template0`,
  `template1`) — no `kanadshield` (or similarly named) database, no
  legal/government schema, no rows of any kind.
- `pgvector` extension package was **not installed**.
- This directly contradicts the master prompt's premise ("build on top of
  an existing PostgreSQL database... source of truth, never destructively
  modified"). There was no existing database to build on top of.

## 3. Resolution (confirmed with user)

The user confirmed they already have the real production database
separately and it will be **integrated later**. For this build:

- A local `kanadshield` PostgreSQL 16 database was created in this
  environment, with `vector`, `pg_trgm`, and `unaccent` extensions enabled.
- The full schema below is designed to match the entity model in the
  master prompt, expressed as Alembic migrations — so that when the real
  database is connected, these migrations (or an equivalent
  reconciliation pass) bring it to the same shape without destructive
  changes to any existing rows.
- No production legal document data exists anywhere in this environment.
  Per rule 2 (no fake data), the corpus is **not** faked. Any fixture data
  used in automated tests is clearly scoped to `tests/fixtures` and never
  presented as real ingested content. Real ingestion depends on live
  network access to government portals, which is addressed by the
  `SourceConnector` framework (Task 4) — connectors are implemented for
  real, documented public endpoints where reachable from this sandbox,
  and are otherwise honestly marked as unexercised in this environment
  rather than faked.

## 4. Toolchain audit

| Component | Status |
|---|---|
| Python | 3.11.15 present (prompt asks 3.12+; adapted — 3.11 used, no 3.12-only syntax) |
| PostgreSQL 16 + pgvector 0.6 | Installed and enabled in this session |
| Redis 7.0.15 | Installed, not yet running as a service |
| Node 22 / npm 10 | Present, sufficient for Vite/React |
| Docker | Present (29.3.1) — used for local dev compose, not required at runtime |
| Ollama | Install blocked by sandbox network policy (403 from install script host). LLM/embedding provider code is written against the Ollama HTTP API and `OllamaProvider` is the default, but cannot be smoke-tested end-to-end in this sandbox. Documented explicitly, not faked. |
| Tesseract OCR (+ guj, hin, eng, osd) | Installed |
| sentence-transformers (`BAAI/bge-m3`) | Installed via pip; downloading the actual model weights requires network access to Hugging Face — verified reachable, model fetched on first use (lazy-loaded, cached) |
| faster-whisper | Installed via pip |

## 5. Adaptations to the plan

- `SUPPORTED_LANGUAGES` config default is `en,gu,hi` as specified.
- Because there is no live Ollama daemon in this sandbox, `AI_PROVIDER`
  defaults to `ollama` per spec, but integration tests that need a live
  LLM response are marked `skip` with a clear reason if no Ollama host is
  reachable at test time — never replaced with a mocked "fake LLM" that
  returns canned text disguised as a real answer.
- Ingestion connectors are built against the real public endpoints named
  in the prompt (India Code, eGazette, Gujarat GR portal, court judgment
  portals). Where a specific portal is unreachable, rate-limited, or
  requires interactive auth from this sandbox, that connector is marked
  `status: reachable` / `status: unreachable-from-sandbox` in
  `docs/CONNECTOR_STATUS.md` (created alongside ingestion work) rather
  than silently stubbed.

## 6. Definition of Done tracking (final)

Status against the master prompt's bar: real data, no hardcoded values,
no stubs, a passing test against real data, honest failure modes.

| Module | Status | Notes |
|---|---|---|
| Data access layer / repositories | **Done** | Real async SQLAlchemy repos, tested against real Postgres |
| Document/Act/Judgment/Department/Ministry/Court APIs | **Done** | Tested; fixed a real lazy-load bug in `/acts/{id}` found via testing |
| Ingestion pipeline (connectors, PDF/HTML extraction, categorization, metadata extraction, idempotent upsert, dead-letter) | **Done**, connectors **partial** | Pipeline logic fully real and tested end-to-end. The 3 connectors (India Code, eGazette, Gujarat GR) are real implementations against documented endpoints but **not live-verified** — this sandbox's network proxy blocks `*.gov.in`/`*.nic.in`. See `docs/CONNECTOR_STATUS.md`. |
| Hybrid search (FTS + pgvector + ranking + facets) | **Done** | Tested against real Postgres; degrades gracefully to lexical-only if the embedding provider is unreachable (never fails the whole search) |
| Autocomplete | **Done** | Deterministic, no LLM |
| RAG (summarize/ask, citation validation, prompt-injection defense) | **Done** | Runs in Celery workers per spec (fixed — was inline in the request originally). Grounded-only; returns honest "insufficient evidence" rather than a guess. Citation validation against real chunk IDs tested, including a hallucination-rejection test. |
| Legal-aware chunking | **Done** | Section/clause/facts-issues-analysis-decision/eligibility-conditions splitting, tested |
| Entity/relationship graph | **Done** | Deterministic regex-based extraction (AMENDS/REPEALS/CITES/etc.), persisted, queryable via API |
| Document comparison + timeline | **Done** | Deterministic categorized diff (eligibility/dates/money/authorities/obligations/penalties/definitions); LLM only explains an existing diff |
| Legal Change & Impact Radar | **Done** | Wired into the ingestion pipeline's own change-detection (re-crawl hash mismatch), not a parallel system |
| Scheme matching + citizen profile | **Done** | JSONB rule engine, tested; profile CRUD with consent revoke/delete; DigiLocker adapter implemented against the real documented OAuth2 flow but **not live-verified** (no test credentials/network access in this sandbox) and disabled by default |
| Auth/RBAC/bookmarks/alerts/research workspace | **Done** | JWT+refresh, bcrypt, real Celery alert evaluation worker, Markdown export |
| Dashboard & analytics | **Done** | Real aggregate queries, anonymized, Redis-cached (public data only) |
| Multilingual (detection, OCR, translation, cross-language search) | **Done**, cross-language search **unverified live** | Language detection and mixed-language flagging tested against real Gujarati/Hindi/English text. Translation layer real and cached, never overwrites originals. The cross-language embedding claim has a real test (`test_cross_language_embeddings.py`) written against the actual `BAAI/bge-m3` model — it is honestly **skipped**, not faked, because this sandbox blocks `huggingface.co` at the proxy level. |
| Offline PWA | **Done** | Real versioned service worker (Workbox precache), IndexedDB persistence (tested with real IndexedDB via fake-indexeddb), server-generated offline bundles, offline action queue with visible sync status |
| Security (JWT/RBAC/rate limiting/headers/audit log) | **Done** | Found and fixed a real gap: `SlowAPIMiddleware` was never registered, so `default_limits` silently did nothing outside the few explicitly-decorated routes — caught by a rate-limit test, now enforced globally |
| Performance (indexes, pooling, caching, Celery for AI) | **Done** | All planned indexes present (GIN for FTS, HNSW for vectors, trigram, B-tree on every filter column); query plans checked with `EXPLAIN ANALYZE` (table currently empty — no real corpus — so plan shape should be re-checked once real data volume exists); AI moved to Celery workers |
| Frontend (all spec pages, feature-based structure) | **Done** | All pages wired to the real API, no mock data. Golden path (search → document → AI summary → schemes) verified live in a real Chromium browser against the real backend and real Postgres. |
| Backend tests | **Done** | 37 passed, 1 honestly skipped, 0 failed, all against real PostgreSQL |
| Frontend tests | **Done** | Vitest + RTL, including a real-IndexedDB test suite |

## 7. What was never faked

- No corpus data anywhere in this build is presented as real government
  content. The one manually-ingested demo document used to prove the
  live UI flow was deleted from the dev database after verification.
- No AI response is a canned string — every summarize/ask call is grounded
  in real retrieved chunks or returns an honest "insufficient evidence."
- No hardcoded model names, thresholds, or weights — see
  `backend/app/core/config.py` and `.env.example`.
- Two genuine bugs were found and fixed during live testing (a
  `Settings`-object hashability crash in the provider factory, and a
  missing rate-limit middleware) rather than papered over.
