import hashlib
import logging
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.intelligence.providers.base import EmbeddingProvider, LLMProvider, OCRProvider
from app.models.document import Document, DocumentChunk, DocumentVersion
from app.models.enums import DocumentType
from app.models.ingestion import IngestionDeadLetter, IngestionRun
from app.repositories.document_repository import DocumentRepository, compute_content_hash
from app.search.chunking import chunk_document_text
from app.services.categorization import classify_document
from app.services.graph_service import extract_and_persist_relationships
from app.services.ingestion.base import FetchedDocument, RawContentFormat, SourceConnector, SourceDocumentRef
from app.services.language_detection import detect_language
from app.services.metadata_extraction import extract_date, extract_department, extract_keywords, infer_jurisdiction
from app.utils.html_extraction import extract_html_structure
from app.utils.pdf_extraction import extract_pdf_text, render_page_to_png

logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(
        self,
        db: AsyncSession,
        settings: Settings,
        llm: LLMProvider,
        embeddings: EmbeddingProvider,
        ocr: OCRProvider,
    ):
        self.db = db
        self.settings = settings
        self.llm = llm
        self.embeddings = embeddings
        self.ocr = ocr
        self.documents = DocumentRepository(db)

    async def _extract_text(self, fetched: FetchedDocument) -> str:
        if fetched.content_format == RawContentFormat.HTML:
            return extract_html_structure(fetched.raw_bytes.decode("utf-8", errors="ignore")).full_text

        result = extract_pdf_text(fetched.raw_bytes)
        ocr_texts: list[str] = []
        for page in result.pages:
            if not page.needs_ocr:
                continue
            try:
                png_bytes = render_page_to_png(fetched.raw_bytes, page.page_number)
                ocr_result = await self.ocr.extract_text(png_bytes, self.settings.supported_languages)
                ocr_texts.append(ocr_result.text)
            except Exception:
                logger.warning("OCR fallback failed for page %s of %s", page.page_number, fetched.source_document_id)
        return "\n\n".join([result.full_text, *ocr_texts]).strip()

    async def _dead_letter(self, connector: SourceConnector, ref: SourceDocumentRef | None, error: Exception, payload: dict):
        self.db.add(
            IngestionDeadLetter(
                source=connector.source_name,
                source_document_id=ref.source_document_id if ref else None,
                source_url=ref.source_url if ref else None,
                error_message=str(error),
                payload=payload,
            )
        )
        await self.db.flush()

    async def ingest_one(self, connector: SourceConnector, ref: SourceDocumentRef) -> Document | None:
        fetched = await connector.fetch_document(ref)
        text = await self._extract_text(fetched)
        content_hash = compute_content_hash(text or fetched.title)

        existing = await self.documents.get_by_natural_key(connector.source_name, ref.source_document_id)
        if existing is not None and existing.content_hash == content_hash:
            return None  # unchanged — idempotent skip, never reprocessed

        lang = detect_language(text, self.settings)
        classification = await classify_document(
            source=connector.source_name, title=fetched.title, text_excerpt=text, llm=self.llm
        )
        department = extract_department(text)
        date_extraction = extract_date(text)
        jurisdiction, state = infer_jurisdiction(source=connector.source_name, department_name=department.name)
        keywords = extract_keywords(text)

        fields = dict(
            title=fetched.title,
            document_type=classification.document_type,
            classification_confidence=classification.confidence,
            classification_method=classification.method,
            jurisdiction=jurisdiction,
            state=state,
            source_language=lang.language,
            language_confidence=lang.confidence,
            is_mixed_language=lang.is_mixed,
            date=date_extraction.value,
            date_confidence=date_extraction.confidence,
            date_extraction_method=date_extraction.method,
            year=date_extraction.value.year if date_extraction.value else None,
            subject=text[:1000] if text else None,
            keywords=keywords,
            source_url=fetched.source_url,
            text_available=bool(text),
            extracted_text=text,
            content_hash=content_hash,
        )

        was_new = existing is None
        document, _ = await self.documents.upsert_by_natural_key(
            source=connector.source_name, source_document_id=ref.source_document_id, **fields
        )

        if not was_new:
            prior_version_count = (
                await self.db.execute(
                    select(func.count()).select_from(DocumentVersion).where(DocumentVersion.document_id == document.id)
                )
            ).scalar_one()
            self.db.add(
                DocumentVersion(
                    document_id=document.id,
                    version_number=prior_version_count + 1,
                    content_hash=content_hash,
                    extracted_text=text,
                )
            )

        await self._rechunk_and_embed(document, text)
        await extract_and_persist_relationships(self.db, document)
        await self.db.flush()
        return document

    async def _rechunk_and_embed(self, document: Document, text: str) -> None:
        if not text:
            return
        await self.db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
        await self.db.flush()

        chunks = chunk_document_text(document_type=document.document_type, text=text, settings=self.settings)
        if not chunks:
            return
        vectors = await self.embeddings.embed([c.text for c in chunks])
        for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
            self.db.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=idx,
                    chunk_type=chunk.chunk_type,
                    text=chunk.text,
                    token_count=len(chunk.text) // 4,
                    section_ref=chunk.section_ref,
                    language=document.source_language,
                    embedding=vector,
                )
            )

    async def run(self, connector: SourceConnector, *, since: str | None = None) -> IngestionRun:
        run = IngestionRun(source=connector.source_name, started_at=datetime.now(timezone.utc), status="running")
        self.db.add(run)
        await self.db.flush()

        try:
            refs = await connector.list_documents(since=since)
        except Exception as exc:
            run.status = "failed"
            run.finished_at = datetime.now(timezone.utc)
            await self._dead_letter(connector, None, exc, {"stage": "list_documents"})
            await self.db.flush()
            return run

        for ref in refs:
            run.documents_seen += 1
            try:
                result = await self.ingest_one(connector, ref)
                if result is None:
                    run.documents_unchanged += 1
                else:
                    run.documents_new += 1
            except Exception as exc:
                await self.db.rollback()
                self.db.add(run)  # re-attach after rollback expired it
                run.documents_failed += 1
                await self._dead_letter(connector, ref, exc, {"stage": "ingest_one"})

        run.status = "completed"
        run.finished_at = datetime.now(timezone.utc)
        await self.db.flush()
        return run
