from fastapi import APIRouter

from app.api.routes import login, project

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(project.router)
api_router.include_router(project.tasks_router)


# if settings.ENVIRONMENT == "local":
#     api_router.include_router(private.router)
