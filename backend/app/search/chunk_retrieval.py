import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.intelligence.providers.base import EmbeddingProvider
from app.models.document import Document, DocumentChunk

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_title: str
    document_source_url: str | None
    text: str
    chunk_type: str
    section_ref: str | None
    page: int | None
    score: float


async def retrieve_chunks(
    db: AsyncSession,
    settings: Settings,
    embeddings: EmbeddingProvider,
    query: str,
    *,
    document_id: uuid.UUID | None = None,
    top_k: int | None = None,
) -> list[RetrievedChunk]:
    """Chunk-level hybrid retrieval used by summarize/ask — the RAG layer
    only ever sees real retrieved chunk text, never whole-document dumps
    or model-memory answers."""
    top_k = top_k or settings.RAG_TOP_K_RETRIEVAL
    try:
        vectors = await embeddings.embed([query])
    except Exception:
        # Embedding provider unavailable — RAG has no evidence to ground an
        # answer on, so callers must see an empty retrieval (leading to an
        # honest "insufficient evidence" response) rather than a 500.
        logger.warning("Embedding provider unavailable during chunk retrieval", exc_info=True)
        return []
    query_vector = vectors[0]

    distance = DocumentChunk.embedding.cosine_distance(query_vector).label("distance")
    ts_query = func.websearch_to_tsquery("english", query)
    lexical_rank = func.coalesce(func.ts_rank(DocumentChunk.search_vector, ts_query), 0.0).label("lexical_rank")

    stmt = (
        select(DocumentChunk, Document, distance, lexical_rank)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(DocumentChunk.embedding.is_not(None))
    )
    if document_id is not None:
        stmt = stmt.where(DocumentChunk.document_id == document_id)
    stmt = stmt.order_by(distance).limit(top_k * 3)

    rows = (await db.execute(stmt)).all()
    if not rows:
        return []

    max_lex = max((float(r.lexical_rank) for r in rows), default=0.0) or 1.0
    scored: list[RetrievedChunk] = []
    for chunk, document, dist, lex_rank in rows:
        semantic = max(0.0, 1.0 - float(dist) / 2.0)
        lexical = float(lex_rank) / max_lex
        score = settings.SEARCH_WEIGHT_SEMANTIC * semantic + settings.SEARCH_WEIGHT_LEXICAL * lexical
        scored.append(
            RetrievedChunk(
                chunk_id=chunk.id,
                document_id=document.id,
                document_title=document.title,
                document_source_url=document.source_url,
                text=chunk.text,
                chunk_type=chunk.chunk_type.value,
                section_ref=chunk.section_ref,
                page=chunk.page,
                score=score,
            )
        )
    scored.sort(key=lambda c: c.score, reverse=True)
    return scored[:top_k]
