from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "kanadshield",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.ingestion_tasks",
        "app.workers.alert_tasks",
        "app.workers.ai_tasks",
    ],
)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.timezone = "UTC"
