"""Expensive AI processing (LLM calls, embedding retrieval) always runs in
a Celery worker, never inline in a synchronous HTTP request — the API
layer only enqueues and polls."""
import asyncio
import uuid

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.intelligence.factory import get_embedding_provider, get_llm_provider
from app.services.rag.ask_service import answer_question
from app.services.rag.summarize_service import SummarizationError, summarize_document
from app.workers.celery_app import celery_app


async def _run_summarize(document_id: str) -> dict:
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    try:
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        async with session_maker() as db:
            try:
                summary = await summarize_document(
                    db, settings, get_llm_provider(), get_embedding_provider(), uuid.UUID(document_id)
                )
                await db.commit()
                return {"status": "success", "result": summary.model_dump()}
            except SummarizationError as exc:
                return {"status": "insufficient_evidence", "error": str(exc)}
    finally:
        await engine.dispose()


async def _run_ask(question: str, document_id: str | None) -> dict:
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    try:
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        async with session_maker() as db:
            answer = await answer_question(
                db,
                settings,
                get_llm_provider(),
                get_embedding_provider(),
                question,
                document_id=uuid.UUID(document_id) if document_id else None,
            )
            await db.commit()
        return {
            "status": "insufficient_evidence" if answer.insufficient_evidence else "success",
            "result": answer.model_dump(),
        }
    finally:
        await engine.dispose()


@celery_app.task(name="ai.summarize_document")
def summarize_document_task(document_id: str) -> dict:
    return asyncio.run(_run_summarize(document_id))


@celery_app.task(name="ai.ask_question")
def ask_question_task(question: str, document_id: str | None = None) -> dict:
    return asyncio.run(_run_ask(question, document_id))
