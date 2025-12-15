"""Project and Task API routes for urban planning GIS platform."""

import json
import shutil
import uuid as uuid_pkg
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from app.api.deps import CurrentUser, SessionDep
from app.api.utils import (validate_geojson_feature_collection, update_project)
from app.definition import StepType, ExtensionType, STEPS
from app.exceptions import ProjectDoesNotExists
from app.models.project import (
    Project,
    ComponentResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectDetailResponse,
    TaskUpdate,
)

router = APIRouter(tags=["Projects"])


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
            name=project.name,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
        for project in projects
    ]


@router.post(
    "/projects", response_model=ProjectDetailResponse, status_code=201
)
def create_project(
        *,
        session: SessionDep,
        current_user: CurrentUser,
        project_in: ProjectCreate,
        request: Request
) -> ProjectDetailResponse:
    """Create a new project with GeoJSON validation."""
    # Create database record
    project = Project.create(
        session=session,
        user=current_user,
        name=project_in.name,
        description=project_in.description or "",
    )
    return update_project(
        project=project, project_in=project_in, session=session
    )


@router.get(
    "/projects/{uuid}",
    status_code=200,
    responses={
        404: ProjectDoesNotExists.response_schema,
    },
)
def get_project_detail(
        *,
        session: SessionDep,
        current_user: CurrentUser,
        uuid: UUID
) -> ProjectDetailResponse:
    """Return project details."""
    try:
        project = Project.get(session=session, user=current_user, uuid=uuid)
    except ProjectDoesNotExists as e:
        raise HTTPException(status_code=404, detail=str(e))

    return ProjectDetailResponse(
        uuid=project.uuid,
        name=project.name,
        description=project.description,
        parameters=project.parameters,
        project_metadata=project.project_metadata,
    )


@router.put(
    "/projects/{uuid}",
    status_code=200,
    responses={
        404: ProjectDoesNotExists.response_schema,
    },
)
def put_project_detail(
        *,
        session: SessionDep,
        current_user: CurrentUser,
        project_in: ProjectCreate,
        uuid: UUID,
        request: Request
) -> ProjectDetailResponse:
    """Return project details."""
    try:
        project = Project.get(session=session, user=current_user, uuid=uuid)
    except ProjectDoesNotExists as e:
        raise HTTPException(status_code=404, detail=str(e))

    return update_project(
        project=project, project_in=project_in, session=session
    )


@router.delete(
    "/projects/{uuid}",
    status_code=204,
    responses={
        404: ProjectDoesNotExists.response_schema,
    },
)
def delete_project(
        *,
        session: SessionDep,
        current_user: CurrentUser,
        uuid: UUID,
        request: Request
) -> None:
    """Delete project and its associated folder."""

    try:
        project = Project.get(session=session, user=current_user, uuid=uuid)
    except ProjectDoesNotExists as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Delete the project from the database
    session.delete(project.project_user)
    session.commit()

    # Delete the project folder from disk
    if project.folder.exists():
        shutil.rmtree(project.folder)
    return None


@router.get(
    "/projects/{uuid}/roads_input.geojson",
    status_code=200,
    responses={
        404: ProjectDoesNotExists.response_schema,
    },
)
def get_roads_file(
        *,
        session: SessionDep,
        current_user: CurrentUser,
        uuid: UUID
) -> FileResponse:
    """Trigger a single step of a project generation task."""
    try:
        project = Project.get(session=session, user=current_user, uuid=uuid)
    except ProjectDoesNotExists as e:
        raise HTTPException(status_code=404, detail=str(e))
    filename = f"roads.geojson"
    file_path = project.get_path_roads()
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found."
        )

    return FileResponse(
        path=file_path,
        media_type="application/geo+json",
        filename=filename,
    )


@router.get(
    "/projects/{uuid}/site_input.geojson",
    status_code=200,
    responses={
        404: ProjectDoesNotExists.response_schema,
    },
)
def get_roads_file(
        *,
        session: SessionDep,
        current_user: CurrentUser,
        uuid: UUID
) -> FileResponse:
    """Trigger a single step of a project generation task."""
    try:
        project = Project.get(session=session, user=current_user, uuid=uuid)
    except ProjectDoesNotExists as e:
        raise HTTPException(status_code=404, detail=str(e))
    filename = f"site.geojson"
    file_path = project.get_path_site()
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found."
        )

    return FileResponse(
        path=file_path,
        media_type="application/geo+json",
        filename=filename,
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
    financial = {}
    financial_file = project.get_file_path(
        step, ExtensionType.JSON, filename="financial.json"
    )
    if Path.exists(financial_file):
        financial = json.loads(financial_file.read_text())
    else:
        # Old financial location
        financial_file = project.get_file_path(
            step, ExtensionType.JSON, filename="result.json"
        )
        if Path.exists(financial_file):
            financial = json.loads(financial_file.read_text())

    url = str(
        request.url_for(
            "get_project_file",
            uuid=project.uuid,
            step=step.value,
            extension=ExtensionType.GLTF.value,
        )
    )
    return ComponentResponse(file=url, task=task, financial=financial)


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
