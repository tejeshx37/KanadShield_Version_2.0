# KanadShield API Contract (Frontend-Authored)

No backend implementation exists in this repository yet. This contract was
authored by the frontend build to unblock real (non-mocked) API integration:
every frontend query hook calls these exact paths/shapes. When a real backend
is implemented, it should conform to this contract, or this document should
be updated to match and the frontend adjusted accordingly.

Base URL: `VITE_API_BASE_URL` (env), e.g. `https://api.kanadshield.example/v1`.
All endpoints are prefixed with this base. Auth: `Authorization: Bearer <token>`
where applicable (omitted below for brevity).

## Conventions

- Paginated list responses: `{ items: T[], total: number, page: number, pageSize: number }`
- Errors: `{ error: { code: string, message: string } }` with non-2xx status.
- Dates: ISO 8601 strings.
- Status pill values: `active | amended | superseded`.
- Severity values: `critical | high | medium | low`.

## Reference data

- `GET /reference/departments` -> `{ id, name, code }[]`
- `GET /reference/document-types` -> `{ id, name }[]`
- `GET /reference/jurisdictions` -> `{ id, name }[]`
- `GET /reference/languages` -> `{ code, label }[]` (drives language switcher)

## Dashboard

- `GET /dashboard/summary?department={id}` ->
  `{ trendingSearches: {term, count}[], frequentDocuments: DocumentSummary[],
     departmentActivity: {departmentId, departmentName, count}[],
     corpusHealth: {classificationConfidenceAvg, extractionConfidenceAvg,
       classificationConfidenceDistribution: {bucket, count}[],
       extractionConfidenceDistribution: {bucket, count}[]} }`
- `GET /users/me/activity?limit=20` -> `ActivityItem[]`
- `GET /users/me/alerts?status=active` -> `Alert[]`

## Research (search + workspace)

- `GET /search?q={q}&department={id}&type={id}&jurisdiction={id}&dateFrom=&dateTo=&page=&pageSize=`
  -> `{ items: SearchResult[], total, page, pageSize,
        facets: { department: FacetCount[], type: FacetCount[], jurisdiction: FacetCount[] } }`
- `GET /search/autocomplete?q={q}` -> `{ suggestions: {label, entityType, entityId}[] }`
- `GET /workspace/collections` -> `Collection[]`
- `POST /workspace/collections` -> `Collection`
- `POST /workspace/collections/{id}/items` body `{ documentId }` -> `Collection`
- `POST /documents/compare` body `{ documentIdA, documentIdB }` ->
  `{ explanation: string, diff: DiffSegment[] }`
  where `DiffSegment = { type: "added"|"removed"|"unchanged"|"modified", text }`

## Archives

- `GET /documents?department=&type=&jurisdiction=&dateFrom=&dateTo=&page=&pageSize=`
  -> `{ items: DocumentSummary[], total, page, pageSize, facets: {...} }`
- `GET /documents/{id}` -> `DocumentDetail`
  `DocumentDetail = { id, title, type, department, jurisdiction, status,
    issuedDate, referenceNumber, sourceUrl, cachedCopyUrl?, summary,
    keyProvisions: string[], metadata: Record<string,string> }`
- `GET /documents/{id}/cross-links` -> `{ type: "issued_under"|"supersedes"|"superseded_by"|"interprets"|"cites",
    document: DocumentSummary }[]`
- `GET /documents/{id}/graph` -> `{ nodes: {id, label, type}[], edges: {source, target, type}[] }`

## Insights

- `GET /insights/change-radar?department=&severity=&page=&pageSize=`
  -> `{ items: ChangeRadarItem[], total, page, pageSize }`
  `ChangeRadarItem = { id, severity, title, whatChanged, publishedAt,
    affectedDocuments: DocumentSummary[] }`
- `GET /insights/timeline?topicId={id}` -> `{ events: {id, type, title, date, documentId}[] }`

## Public Service (Schemes + Citizen Entitlement)

- `GET /schemes?department=&page=&pageSize=` -> `{ items: Scheme[], total, page, pageSize }`
- `GET /schemes/{id}` -> `SchemeDetail`
- `POST /entitlement/profile/manual` body `{ ageRange, state, incomeRange, occupation, ... }`
  -> `{ profileId }`
- `GET /entitlement/digilocker/start` -> `{ redirectUrl }` (only when `DIGILOCKER_ENABLED=true`)
- `GET /entitlement/digilocker/callback?code=&state=` -> `{ profileId, verifiedAttributes: string[] }`
- `POST /entitlement/digilocker/revoke` -> `{ success: true }`
- `DELETE /entitlement/profile/{profileId}` -> `{ success: true }`
- `GET /entitlement/matches?profileId={id}` -> `{ items: SchemeMatch[] }`
  `SchemeMatch = { scheme: Scheme, matchedConditions: string[], missingConditions: string[],
    requiredDocuments: string[], sourceUrl: string }`

## Library

- `GET /users/me/bookmarks` / `POST` / `DELETE /users/me/bookmarks/{id}`
- `GET /users/me/saved-searches` / `POST` / `DELETE /users/me/saved-searches/{id}`
- `GET /users/me/alerts` / `POST` / `PATCH /users/me/alerts/{id}` (subscribe/unsubscribe)
- Offline manager reads/writes IndexedDB directly on the client; no backend
  round-trip beyond `GET /documents/{id}/bundle` to fetch a downloadable bundle.

## Support (AI Ask)

- `POST /ask` body `{ question }` ->
  `{ status: "answered"|"insufficient_evidence", answer?: string,
     citations: { documentId, title, snippet }[] }`

## Shared types

```
DocumentSummary = { id, title, type, department, jurisdiction, status, issuedDate, referenceNumber }
FacetCount = { id, label, count }
ActivityItem = { id, type, description, timestamp, documentId? }
Alert = { id, title, description, createdAt, severity }
Collection = { id, name, documentIds: string[] }
Scheme = { id, name, department, summary, sourceUrl }
```
