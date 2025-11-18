"""Project and Task API routes for urban planning GIS platform."""

import uuid as uuid_pkg
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from app.api.deps import SessionDep
from app.models.project import (
    ComponentResponse,
    ComponentType,
    ExtensionType,
    ProjectCreate,
    ProjectResponse
)

router = APIRouter(tags=["Projects"])


def validate_geojson_feature_collection(
        data: dict[str, Any],
        geometry_type: str
) -> None:
    """Validate GeoJSON FeatureCollection structure."""
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=400,
            detail=f"Expected GeoJSON FeatureCollection, got {type(data)}"
        )

    if data.get("type") != "FeatureCollection":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Expected type 'FeatureCollection', "
                f"got '{data.get('type')}'"
            )
        )

    features = data.get("features", [])
    if not isinstance(features, list):
        raise HTTPException(status_code=400, detail="Features must be a list")

    if not features:
        raise HTTPException(
            status_code=400,
            detail=f"At least one {geometry_type} feature is required"
        )

    for idx, feature in enumerate(features):
        if not isinstance(feature, dict):
            raise HTTPException(
                status_code=400, detail=f"Feature {idx} must be an object"
            )

        geometry = feature.get("geometry")
        if not geometry:
            raise HTTPException(
                status_code=400, detail=f"Feature {idx} missing geometry"
            )

        geom_type = geometry.get("type")
        if geom_type != geometry_type:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Expected geometry type '{geometry_type}', "
                    f"got '{geom_type}' in feature {idx}"
                ),
            )


@router.post("/projects", response_model=ProjectResponse, status_code=201)
def create_project(
        *, session: SessionDep, project_in: ProjectCreate, request: Request
) -> ProjectResponse:
    """Create a new project with GeoJSON validation."""
    project = Project(uuid=uuid_pkg.uuid4())

    if project_in.site is not None:
        validate_geojson_feature_collection(project_in.site, "Polygon")

    if project_in.roads is not None:
        validate_geojson_feature_collection(project_in.roads, "LineString")

    parameters_dict = project_in.parameters.model_dump() if project_in.parameters else {}

    project.name = project_in.name
    project.description = project_in.description or ""
    project.project_metadata = project_in.project_metadata or {}
    project.parameters = parameters_dict
    project.save_to_file()

    # Run task
    project.generate()
    url = str(
        request.url_for(
            "get_project_file",
            uuid=project.uuid,
            step="site",
            extension=ExtensionType.GLTF.value,
        )
    )
    return ProjectResponse(
        project_uuid=project.uuid,
        project_name=project_in.name,
        file=url,
    )


@router.get(
    "/projects/{uuid}/{step}.{extension}",
    status_code=202,
)
def get_project_file(
        *,
        session: SessionDep,
        uuid: UUID,
        step: ComponentType,
        extension: ExtensionType,
) -> FileResponse:
    """Trigger a single step of a project generation task."""
    project = Project(uuid=uuid)
    filename = f"{step.value}.{extension.value}"
    file_path = project.get_file_path(step, extension)
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found."
        )

    return FileResponse(
        path=file_path,
        media_type="application/geo+json"
        if extension == ExtensionType.GEOJSON.value
        else "model/gltf+json",
        filename=filename,
    )


@router.get(
    "/projects/{uuid}/{step}",
    response_model=ComponentResponse,
    status_code=202,
)
def get_step_data(
        *,
        session: SessionDep,
        uuid: UUID,
        step: ComponentType,
        request: Request
) -> ComponentResponse:
    """Get sttp data."""
    url = str(
        request.url_for(
            "get_project_file",
            uuid=uuid,
            step=step,
            extension=ExtensionType.GLTF.value,
        )
    )
    return ComponentResponse(file=url, lucky_sheet={})
