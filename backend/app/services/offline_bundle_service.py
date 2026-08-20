import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.intelligence.providers.base import EmbeddingProvider, LLMProvider
from app.repositories.document_repository import DocumentRepository
from app.services.rag.summarize_service import SummarizationError, summarize_document

logger = logging.getLogger(__name__)


async def build_offline_bundle(
    db: AsyncSession,
    settings: Settings,
    llm: LLMProvider,
    embeddings: EmbeddingProvider,
    document_ids: list[uuid.UUID],
) -> dict:
    """Generates a real downloadable bundle (documents + metadata +
    pre-generated summaries) entirely server-side, online, before the
    client ever sees it — summarization is never attempted on-device."""
    repo = DocumentRepository(db)
    items = []
    for document_id in document_ids:
        document = await repo.get(document_id)
        if document is None:
            continue
        summary = None
        try:
            summary = await summarize_document(db, settings, llm, embeddings, document_id)
        except SummarizationError:
            # Honest partial bundle: the document downloads without a
            # summary rather than a fabricated one.
            logger.info("No summary available for offline bundle of document %s", document_id)

        items.append(
            {
                "document": {
                    "id": str(document.id),
                    "title": document.title,
                    "document_type": document.document_type.value,
                    "jurisdiction": document.jurisdiction.value,
                    "state": document.state,
                    "date": document.date.isoformat() if document.date else None,
                    "source_url": document.source_url,
                    "extracted_text": document.extracted_text,
                    "subject": document.subject,
                },
                "summary": summary.model_dump() if summary else None,
            }
        )

    return {"generated_at": datetime.now(timezone.utc).isoformat(), "items": items}
