import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import Float, and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.intelligence.providers.base import EmbeddingProvider
from app.models.document import Document, DocumentChunk
from app.models.enums import DocumentType, Jurisdiction
from app.models.users import SearchHistory

_LEXICAL_TS_CONFIG = {"en": "english", "gu": "simple", "hi": "simple"}
logger = logging.getLogger(__name__)


@dataclass
class SearchFilters:
    source: str | None = None
    document_type: DocumentType | None = None
    jurisdiction: Jurisdiction | None = None
    ministry_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None
    court_id: uuid.UUID | None = None
    year_from: int | None = None
    year_to: int | None = None
    date_from: date | None = None
    date_to: date | None = None
    language: str | None = None


@dataclass
class SearchResultItem:
    document_id: uuid.UUID
    title: str
    document_type: str
    jurisdiction: str
    state: str | None
    date: date | None
    source_url: str | None
    snippet: str
    score: float
    lexical_score: float
    semantic_score: float


@dataclass
class SearchResponse:
    items: list[SearchResultItem]
    total: int
    facets: dict = field(default_factory=dict)
    search_time_ms: float = 0.0


def _authority_weight(settings: Settings, document_type: DocumentType) -> float:
    weights = json.loads(settings.AUTHORITY_WEIGHTS_JSON)
    return float(weights.get(document_type.value, weights.get("OTHER", 0.2)))


class HybridSearchService:
    """Lexical (PostgreSQL FTS) + semantic (pgvector) + metadata/authority/
    freshness merge. Weights are all sourced from Settings — never inline
    literals — so ranking behavior is tunable per environment."""

    def __init__(self, db: AsyncSession, settings: Settings, embeddings: EmbeddingProvider):
        self.db = db
        self.settings = settings
        self.embeddings = embeddings

    def _apply_filters(self, stmt, filters: SearchFilters):
        if filters.source:
            stmt = stmt.where(Document.source == filters.source)
        if filters.document_type:
            stmt = stmt.where(Document.document_type == filters.document_type)
        if filters.jurisdiction:
            stmt = stmt.where(Document.jurisdiction == filters.jurisdiction)
        if filters.ministry_id:
            stmt = stmt.where(Document.ministry_id == filters.ministry_id)
        if filters.department_id:
            stmt = stmt.where(Document.department_id == filters.department_id)
        if filters.court_id:
            stmt = stmt.where(Document.court_id == filters.court_id)
        if filters.year_from:
            stmt = stmt.where(Document.year >= filters.year_from)
        if filters.year_to:
            stmt = stmt.where(Document.year <= filters.year_to)
        if filters.date_from:
            stmt = stmt.where(Document.date >= filters.date_from)
        if filters.date_to:
            stmt = stmt.where(Document.date <= filters.date_to)
        if filters.language:
            stmt = stmt.where(Document.source_language == filters.language)
        return stmt

    async def _lexical_scores(self, query: str, filters: SearchFilters, limit: int) -> dict[uuid.UUID, float]:
        ts_config = _LEXICAL_TS_CONFIG.get(filters.language or "en", "english")
        ts_query = func.websearch_to_tsquery(ts_config, query)
        rank = func.ts_rank(Document.search_vector, ts_query).label("rank")
        stmt = select(Document.id, rank).where(Document.search_vector.op("@@")(ts_query))
        stmt = self._apply_filters(stmt, filters).order_by(rank.desc()).limit(limit)
        rows = (await self.db.execute(stmt)).all()
        return {row.id: float(row.rank) for row in rows}

    async def _semantic_scores(self, query: str, filters: SearchFilters, limit: int) -> dict[uuid.UUID, float]:
        vectors = await self.embeddings.embed([query])
        query_vector = vectors[0]
        distance = DocumentChunk.embedding.cosine_distance(query_vector).label("distance")
        stmt = (
            select(DocumentChunk.document_id, func.min(distance).label("min_distance"))
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(DocumentChunk.embedding.is_not(None))
        )
        stmt = self._apply_filters(stmt, filters)
        stmt = stmt.group_by(DocumentChunk.document_id).order_by("min_distance").limit(limit)
        rows = (await self.db.execute(stmt)).all()
        # cosine_distance in [0, 2]; convert to a similarity score in [0, 1].
        return {row.document_id: max(0.0, 1.0 - float(row.min_distance) / 2.0) for row in rows}

    async def _facets(self, filters: SearchFilters) -> dict:
        stmt = select(Document.document_type, func.count()).group_by(Document.document_type)
        stmt = self._apply_filters(stmt, filters)
        type_rows = (await self.db.execute(stmt)).all()

        stmt2 = select(Document.jurisdiction, func.count()).group_by(Document.jurisdiction)
        stmt2 = self._apply_filters(stmt2, filters)
        juris_rows = (await self.db.execute(stmt2)).all()

        return {
            "document_type": {row[0].value: row[1] for row in type_rows},
            "jurisdiction": {row[0].value: row[1] for row in juris_rows},
        }

    async def search(
        self, query: str, filters: SearchFilters, *, page: int, page_size: int, user_id: uuid.UUID | None = None
    ) -> SearchResponse:
        start = time.perf_counter()
        candidate_limit = max(self.settings.RAG_TOP_K_RETRIEVAL * 3, page * page_size * 3)

        lexical_scores = await self._lexical_scores(query, filters, candidate_limit) if query.strip() else {}
        semantic_scores: dict[uuid.UUID, float] = {}
        if query.strip():
            try:
                semantic_scores = await self._semantic_scores(query, filters, candidate_limit)
            except Exception:
                # The embedding provider (e.g. a local model download, or a
                # remote Ollama/OpenAI-compatible host) is a real external
                # dependency that can be unavailable. Degrade to lexical-only
                # rather than failing the whole search — never fake semantic
                # results, just honestly skip that signal and log why.
                logger.warning("Semantic search unavailable, falling back to lexical-only", exc_info=True)

        candidate_ids = set(lexical_scores) | set(semantic_scores)
        if not candidate_ids:
            base_stmt = self._apply_filters(select(Document.id), filters).limit(candidate_limit)
            candidate_ids = {row[0] for row in (await self.db.execute(base_stmt)).all()}

        if not candidate_ids:
            return SearchResponse(items=[], total=0, facets=await self._facets(filters), search_time_ms=0.0)

        max_lex = max(lexical_scores.values(), default=1.0) or 1.0
        docs_stmt = select(Document).where(Document.id.in_(candidate_ids))
        documents = (await self.db.execute(docs_stmt)).scalars().all()

        current_year = date.today().year
        scored: list[SearchResultItem] = []
        w = self.settings
        for doc in documents:
            lex = lexical_scores.get(doc.id, 0.0) / max_lex
            sem = semantic_scores.get(doc.id, 0.0)
            authority = _authority_weight(w, doc.document_type)
            freshness = 1.0 / (1.0 + max(0, current_year - (doc.year or current_year)))
            metadata_boost = 1.0 if query.lower() in (doc.title or "").lower() else 0.0

            score = (
                w.SEARCH_WEIGHT_LEXICAL * lex
                + w.SEARCH_WEIGHT_SEMANTIC * sem
                + w.SEARCH_WEIGHT_METADATA * metadata_boost
                + w.SEARCH_WEIGHT_AUTHORITY * authority
                + w.SEARCH_WEIGHT_FRESHNESS * freshness
            )
            snippet = (doc.subject or doc.extracted_text or "")[:300]
            scored.append(
                SearchResultItem(
                    document_id=doc.id,
                    title=doc.title,
                    document_type=doc.document_type.value,
                    jurisdiction=doc.jurisdiction.value,
                    state=doc.state,
                    date=doc.date,
                    source_url=doc.source_url,
                    snippet=snippet,
                    score=score,
                    lexical_score=lex,
                    semantic_score=sem,
                )
            )

        scored.sort(key=lambda r: r.score, reverse=True)
        total = len(scored)
        start_idx = (page - 1) * page_size
        page_items = scored[start_idx : start_idx + page_size]

        if query.strip():
            self.db.add(
                SearchHistory(user_id=user_id, query=query, filters=_filters_to_dict(filters), result_count=total)
            )
            await self.db.flush()

        elapsed_ms = (time.perf_counter() - start) * 1000
        return SearchResponse(
            items=page_items, total=total, facets=await self._facets(filters), search_time_ms=elapsed_ms
        )


def _filters_to_dict(filters: SearchFilters) -> dict:
    return {
        k: (v.value if hasattr(v, "value") else (str(v) if v is not None else None))
        for k, v in filters.__dict__.items()
        if v is not None
    }
