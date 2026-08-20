# Ingestion Connector Status

Verified in this development sandbox as of 2026-08-20. The sandbox's
outbound network proxy allowlists only developer-tooling domains (PyPI,
npm, GitHub, Hugging Face, Anthropic); all `*.gov.in`, `*.nic.in`, and
`*.gujarat.gov.in` domains are rejected at the proxy with `403 Forbidden`
before any request reaches the real government host. This is a sandbox
policy restriction, not a statement about the real sites' availability.

| Connector | Source | Reachability from this sandbox | Parsing logic exercised |
|---|---|---|---|
| `IndiaCodeConnector` | `indiacode.nic.in` | Blocked by sandbox proxy policy | Unit-tested against synthetic HTML fixtures only |
| `EGazetteConnector` | `egazette.gov.in` | Blocked by sandbox proxy policy | Unit-tested against synthetic HTML fixtures only |
| `GujaratGRConnector` | `gr.gujarat.gov.in` | Blocked by sandbox proxy policy | Full pipeline (fetch→extract→categorize→chunk→embed) exercised via `tests/test_ingestion_pipeline.py` using an in-memory fake connector serving synthetic GR-shaped HTML — never presented as real government data |

## What this means

- The `SourceConnector` interface, the idempotent upsert pipeline
  (`app/services/ingestion/pipeline.py`), categorization, metadata
  extraction, and legal-aware chunking are real, working code, verified
  end-to-end against a real local PostgreSQL database.
- The three connectors' HTML selectors are written against each portal's
  publicly documented page structure, but could not be live-verified
  against the actual current markup from this sandbox. When deployed in
  an environment with unrestricted outbound access, the first live run
  should be treated as a verification pass — selector mismatches would
  surface as `list_documents()` returning zero refs or as dead-letter
  entries, not as silent fake success, because the pipeline never
  fabricates ingested content.
- Adding a further source (another state, another ministry) requires only
  a new connector class registered in
  `app/services/ingestion/registry.py` plus a `SOURCE_<NAME>_BASE_URL`
  config entry — no changes to `IngestionPipeline`.
