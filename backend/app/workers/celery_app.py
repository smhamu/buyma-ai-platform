from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "buyma_ai_platform",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.embedding_tasks",
        "app.workers.embedding_recovery_tasks",
        "app.workers.supplier_policy_review_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Tokyo",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=120,
    task_time_limit=180,
)

celery_app.conf.beat_schedule = {
    "recover-stale-embedding-jobs": {
        "task": "embedding.recover_stale_jobs",
        "schedule": 60.0,
    },
    "evaluate-supplier-policy-reviews": {
        "task": "supplier_policy_review.evaluate",
        "schedule": 3600.0,
    },
}
