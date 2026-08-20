import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.intelligence.factory import get_embedding_provider, get_llm_provider, get_ocr_provider
from app.services.ingestion.pipeline import IngestionPipeline
from app.services.ingestion.registry import get_enabled_connectors
from app.workers.celery_app import celery_app


async def _run_source(source_name: str) -> dict:
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    connectors = {c.source_name: c for c in get_enabled_connectors(settings)}
    connector = connectors.get(source_name)
    if connector is None:
        await engine.dispose()
        raise ValueError(f"Unknown or disabled ingestion source: {source_name}")

    async with session_maker() as session:
        pipeline = IngestionPipeline(
            session,
            settings,
            get_llm_provider(),
            get_embedding_provider(),
            get_ocr_provider(),
        )
        run = await pipeline.run(connector)
        await session.commit()
        result = {
            "source": run.source,
            "status": run.status,
            "documents_seen": run.documents_seen,
            "documents_new": run.documents_new,
            "documents_unchanged": run.documents_unchanged,
            "documents_failed": run.documents_failed,
        }
    await engine.dispose()
    return result


@celery_app.task(name="ingestion.run_source")
def run_ingestion_for_source(source_name: str) -> dict:
    """Runs one connector's ingestion cycle. Scheduled periodically per
    source via Celery beat (see docs for the beat schedule config), or
    triggered manually through the admin API."""
    return asyncio.run(_run_source(source_name))


@celery_app.task(name="ingestion.run_all")
def run_ingestion_for_all_sources() -> list[dict]:
    settings = get_settings()
    return [run_ingestion_for_source(name) for name in settings.enabled_ingestion_sources]
