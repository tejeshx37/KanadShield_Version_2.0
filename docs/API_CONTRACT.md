# API Contract — Reconciled with the Real Backend

This document originally described a contract the frontend invented before
any backend existed in this repo. A separate branch has since added a real
FastAPI backend (`backend/`), and the frontend has been rewired to call it
directly. **This file is now historical** — the authoritative source for
routes and shapes is the backend itself:

- Routers: `backend/app/api/v1/*.py` (mounted under `/api/v1`, see
  `backend/app/core/config.py:API_V1_PREFIX`)
- Response shapes: `backend/app/schemas/*.py` and the dict literals returned
  directly by routes without a `response_model`
- Frontend-side mirror of those shapes: `frontend/src/api/types.ts`

## Notable real-backend behaviors the frontend accounts for

- **Errors**: `{"error": {"code": str, "message": str}}` on non-2xx — matches
  what was originally assumed here.
- **AI summarize/ask are async jobs**, not synchronous responses: `POST
  /ai/summarize/{document_id}` and `POST /ai/ask` return `{job_id, status:
  "queued"}` (202); poll `GET /ai/jobs/{job_id}` until it settles
  (`pending` → `success` | `failed` | `insufficient_evidence`). See
  `frontend/src/api/hooks.ts:useDocumentAiSummary`.
- **No document status field.** The backend has no Active/Amended/Superseded
  column. The frontend derives it honestly from real relationship-graph
  edges (`SUPERSEDES`/`AMENDS`, see `frontend/src/lib/documentGraph.ts`)
  instead of inventing one.
- **Document type / jurisdiction are fixed Python enums**, not API-served
  reference data — there's no `/reference/*` list endpoint for them, so
  they're mirrored as constants in `frontend/src/lib/referenceData.ts`
  (kept in sync with `backend/app/models/enums.py`).
- **Graph is keyed by an internal entity id**, not a document id — no
  existing route resolved one to the other, so a small endpoint was added:
  `GET /graph/documents/{document_id}` (see `backend/app/services/
  graph_service.py:get_document_graph`), used for both the Cross-Linked
  Documents panel and the Legal Knowledge Graph view.
- **`/documents` (Archives list) has no facet counts and no department
  filter** — only `/search` does. Archives filters by type/jurisdiction/
  state/year; Research's department filter uses `/search?department=<uuid>`
  against `/departments`.
- **Personalized endpoints require auth** (`/search-history`, `/alerts`,
  `/bookmarks`, `/saved-searches`) and there is no login UI built yet, so
  they currently return a real 401 — surfaced as "Sign in required" rather
  than a generic error (see `DashboardPage.tsx:AuthGatedState`).

## Not yet reconciled

Insights (Change Radar / Timeline / Comparison), Public Service (Schemes +
DigiLocker), Library, and Support are still routed placeholders per the
frontend's Definition of Done — the backend has real endpoints for several
of these (`change_radar.py`, `schemes.py`, `citizens.py`, `timeline.py`,
`compare.py`) that a future pass should wire up.
