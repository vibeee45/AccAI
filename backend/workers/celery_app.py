from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "accai",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "workers.import_worker",
    ],
)


celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)