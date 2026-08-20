"""Celery tasks for evaluating saved alerts against newly ingested/changed
documents."""
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.users import Alert
from app.services.alert_evaluation import evaluate_alert
from app.workers.celery_app import celery_app


async def _run_all_alerts() -> dict:
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    matched_total = 0
    alerts_checked = 0
    async with session_maker() as session:
        alerts = (await session.execute(select(Alert).where(Alert.is_active.is_(True)))).scalars().all()
        for alert in alerts:
            matches = await evaluate_alert(session, alert)
            matched_total += len(matches)
            alerts_checked += 1
        await session.commit()
    await engine.dispose()
    return {"alerts_checked": alerts_checked, "documents_matched": matched_total}


@celery_app.task(name="alerts.evaluate_all")
def evaluate_all_alerts() -> dict:
    """Scheduled periodically via Celery beat — evaluates every active
    alert against real data, never a simulated trigger."""
    return asyncio.run(_run_all_alerts())
