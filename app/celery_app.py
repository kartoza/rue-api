from app.core.config import settings
from celery import Celery

REDIS_URL = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:6379"

celery = Celery(
    "worker",
    broker=f"{REDIS_URL}/0",
    backend=f"{REDIS_URL}/1",
    include=["app.tasks.generate_rue"],
)

celery.autodiscover_tasks(["app.tasks"])
