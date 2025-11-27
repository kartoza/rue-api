"""Project and Task API routes for urban planning GIS platform."""

import json
import uuid as uuid_pkg
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from app.api.deps import CurrentUser, SessionDep
from app.exceptions import ProjectDoesNotExists
from app.models.project import (
    Project,
    ComponentResponse,
    ProjectCreate,
    ProjectResponse,
    TaskUpdate
)
from app.types import StepType, ExtensionType, STEPS

router = APIRouter(tags=["Projects"])


def validate_geojson_feature_collection(
        data: dict[str, Any],
        geometry_type: str = None
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
        if geometry_type and geom_type != geometry_type:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Expected geometry type '{geometry_type}', "
                    f"got '{geom_type}' in feature {idx}"
                ),
            )


@router.get("/projects", response_model=list[ProjectResponse], status_code=200)
def get_projects(
        *,
        session: SessionDep,
        current_user: CurrentUser,
) -> list[ProjectResponse]:
    """Return user projects."""
    from sqlmodel import select
    from app.models.project_model import ProjectUser

    query = select(ProjectUser).where(ProjectUser.user_id == current_user.id)
    projects = session.exec(query).all()
    
    return [
        ProjectResponse(
            uuid=project.uuid,
            name=project.name
        )
        for project in projects
    ]


@router.post("/projects", response_model=ProjectResponse, status_code=201)
def create_project(
        *,
        session: SessionDep,
        current_user: CurrentUser,
        project_in: ProjectCreate,
        request: Request
) -> ProjectResponse:
    """Create a new project with GeoJSON validation."""
    # Create database record
    project = Project.create(
        session=session,
        user=current_user,
        name=project_in.name,
        description=project_in.description or "",
    )

    if project_in.site is not None:
        validate_geojson_feature_collection(project_in.site, "Polygon")
        project.save_site(project_in.site)

    if project_in.roads is not None:
        validate_geojson_feature_collection(project_in.roads, "LineString")
        project.save_roads(project_in.roads)

    project.project_metadata = project_in.project_metadata or {}
    project.insert_parameters(project_in.parameters)
    project.update(session=session)

    # Run task
    project.generate()
    return ProjectResponse(
        uuid=project.uuid,
        name=project_in.name
    )


@router.get(
    "/projects/{uuid}/{step}.{extension}",
    status_code=200,
    responses={
        404: ProjectDoesNotExists.response_schema,
    },
)
def get_project_file(
        *,
        session: SessionDep,
        current_user: CurrentUser,
        uuid: UUID,
        step: StepType,
        extension: ExtensionType,
) -> FileResponse:
    """Trigger a single step of a project generation task."""
    try:
        project = Project.get(session=session, user=current_user, uuid=uuid)
    except ProjectDoesNotExists as e:
        raise HTTPException(status_code=404, detail=str(e))
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
    status_code=200,
    responses={
        404: ProjectDoesNotExists.response_schema,
    },
)
def get_step_data(
        *,
        session: SessionDep,
        current_user: CurrentUser,
        uuid: UUID,
        step: StepType,
        request: Request
) -> ComponentResponse:
    """Get sttp data."""
    try:
        project = Project.get(session=session, user=current_user, uuid=uuid)
    except ProjectDoesNotExists as e:
        raise HTTPException(status_code=404, detail=str(e))
    data_file = project.get_file_path(
        step, ExtensionType.JSON, filename="task.json"
    )

    if Path.exists(data_file):
        data = json.loads(data_file.read_text())
        task = {
            "task_id": data["task_id"] or uuid_pkg.uuid4(),
            "status": data["status"],
            "message": data["message"]
        }
    else:
        raise HTTPException(status_code=404, detail="Task does not exist.")

    # Results
    result = {}
    result_file = project.get_file_path(
        step, ExtensionType.JSON, filename="result.json"
    )
    if Path.exists(result_file):
        result = json.loads(result_file.read_text())

    url = str(
        request.url_for(
            "get_project_file",
            uuid=project.uuid,
            step=step.value,
            extension=ExtensionType.GLTF.value,
        )
    )
    return ComponentResponse(file=url, task=task, result=result)


@router.put(
    "/projects/{uuid}/{step}",
    status_code=204,
    responses={
        404: ProjectDoesNotExists.response_schema,
    },
)
def put_step_data(
        *,
        session: SessionDep,
        current_user: CurrentUser,
        uuid: UUID,
        step: StepType,
        task_update: TaskUpdate
) -> None:
    """Update the step data.

    Mostly update the geojson output.
    So it can regenerate the files.
    """
    try:
        project = Project.get(session=session, user=current_user, uuid=uuid)
    except ProjectDoesNotExists as e:
        raise HTTPException(status_code=404, detail=str(e))

    data_file = project.get_file_path(
        step, ExtensionType.JSON, filename="task.json"
    )

    if not Path.exists(data_file):
        raise HTTPException(status_code=404, detail="Task does not exist.")

    if task_update.geojson is None:
        raise HTTPException(
            status_code=400, detail="geojson is required on payload."
        )
    validate_geojson_feature_collection(task_update.geojson)
    filename = project.get_file_path(step, ExtensionType.GEOJSON)
    filename.write_text(json.dumps(task_update.geojson, indent=2))

    # Remove all folders after the current step
    step_idx = STEPS.index(step.value)
    project.remove_step_after(step)

    project.generate(step_idx=step_idx + 1)
    return None
