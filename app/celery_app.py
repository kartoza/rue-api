from celery import Celery
from app.core.config import settings

celery = Celery(
    "worker",
    broker=f"{settings.REDIS_HOST}://{settings.REDIS_PASSWORD}:6379/0",
    backend=f"{settings.REDIS_HOST}://{settings.REDIS_PASSWORD}:6379/1",
    include=[
        "app.tasks.generate_rue",
    ],
)

celery.autodiscover_tasks(["app.tasks"])
