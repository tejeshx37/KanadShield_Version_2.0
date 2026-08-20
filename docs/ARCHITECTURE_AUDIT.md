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

## 6. Definition of Done tracking

See the running task list and the final session summary for per-module
status (done / partial / not done) against the bar defined in the master
prompt's Testing & Definition of Done section.
