import sentry_sdk
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings


def custom_generate_unique_id(route: APIRoute) -> str:
    if route.tags:
        return f"{route.tags[0]}-{route.name}"
    return route.name


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for urban planning and GIS operations with FastAPI backend",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    generate_unique_id_function=custom_generate_unique_id,
    servers=[
        {"url": "http://localhost:8000", "description": "Development server"},
        {"url": "https://api.urbanplanning.com", "description": "Production server"},
    ],
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root URL to API documentation."""
    return RedirectResponse(url=f"{settings.API_V1_STR}/docs")


# Component to directory mapping
COMPONENT_DIRS = {
    "site": "00-site",
    "streets": "01-streets",
    "clusters": "02-clusters",
    "public": "03-public",
    "subdivision": "04-subdivision",
    "footprint": "05-footprint",
    "building_start": "06-building_start",
    "building_max": "07-building_max",
}


@app.get(f"{settings.API_V1_STR}/openapi.yaml", include_in_schema=False)
async def get_custom_openapi_yaml():
    """Serve the custom OpenAPI YAML specification."""
    yaml_path = Path(__file__).parent / "mock" / "swagger.yml"
    if yaml_path.exists():
        return FileResponse(yaml_path, media_type="application/x-yaml")
    raise HTTPException(status_code=404, detail="OpenAPI YAML not found")


@app.get("/files/{filename}", tags=["files"])
async def serve_gltf_file(filename: str) -> FileResponse:
    """Serve GLTF files from mock directories."""
    component = filename.replace(".gltf", "")
    component_dir = COMPONENT_DIRS.get(component)
    if not component_dir:
        raise HTTPException(status_code=404, detail=f"Component '{component}' not found")

    base_dir = Path(__file__).parent
    file_path = base_dir / "mock" / component_dir / "outputs" / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found in {component_dir}"
        )

    return FileResponse(
        path=file_path,
        media_type="model/gltf+json",
        filename=filename,
    )
