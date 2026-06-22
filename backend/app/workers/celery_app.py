from celery import Celery
from app.config import settings

celery_app = Celery(
    "tdportal",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks", "app.workers.conversion_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_max_tasks_per_child=50,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
