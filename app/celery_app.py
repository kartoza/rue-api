from celery import Celery

celery = Celery(
    "worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
    include=[
        "app.tasks.generate_rue",
    ],
)

celery.autodiscover_tasks(["app.tasks"])
