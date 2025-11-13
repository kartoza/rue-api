"""Project and Task API routes for urban planning GIS platform."""

import random
import uuid as uuid_pkg
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from app.api.deps import SessionDep
from app.models.project import (
    ComponentResponse,
    ComponentType,
    Project,
    ProjectCreate,
    ProjectResponse,
    Task,
    TaskCreateResponse,
    TaskPublic,
    TaskStatus,
)

router = APIRouter(tags=["Projects"])
tasks_router = APIRouter(tags=["Tasks"])

# Mock task UUIDs - consistent across requests for same component
MOCK_TASK_UUIDS = {
    "streets": UUID("a1b2c3d4-e5f6-4789-a012-345678901234"),
    "clusters": UUID("b2c3d4e5-f6a7-4890-b123-456789012345"),
    "public": UUID("c3d4e5f6-a7b8-4901-c234-567890123456"),
    "subdivision": UUID("d4e5f6a7-b8c9-4012-d345-678901234567"),
    "footprint": UUID("e5f6a7b8-c9d0-4123-e456-789012345678"),
    "building_start": UUID("f6a7b8c9-d0e1-4234-f567-890123456789"),
    "building_max": UUID("a7b8c9d0-e1f2-4345-a678-901234567890"),
}

# Mock project UUID
MOCK_PROJECT_UUID = UUID("123e4567-e89b-12d3-a456-426614174001")

# Component to directory mapping
COMPONENT_DIRS = {
    "streets": "01-streets",
    "clusters": "02-clusters",
    "public": "03-public",
    "subdivision": "04-subdivision",
    "footprint": "05-footprint",
    "building_start": "06-building_start",
    "building_max": "07-building_max",
}


def get_file_url(request: Request, component: str) -> str:
    """Generate file URL for a component."""
    return f"{request.url.scheme}://{request.url.netloc}/files/{component}.gltf"


def validate_geojson_feature_collection(data: dict[str, Any], geometry_type: str) -> None:
    """Validate GeoJSON FeatureCollection structure."""
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=400, detail=f"Expected GeoJSON FeatureCollection, got {type(data)}"
        )

    if data.get("type") != "FeatureCollection":
        raise HTTPException(
            status_code=400, detail=f"Expected type 'FeatureCollection', got '{data.get('type')}'"
        )

    features = data.get("features", [])
    if not isinstance(features, list):
        raise HTTPException(status_code=400, detail="Features must be a list")

    if not features:
        raise HTTPException(status_code=400, detail=f"At least one {geometry_type} feature is required")

    for idx, feature in enumerate(features):
        if not isinstance(feature, dict):
            raise HTTPException(status_code=400, detail=f"Feature {idx} must be an object")

        geometry = feature.get("geometry")
        if not geometry:
            raise HTTPException(status_code=400, detail=f"Feature {idx} missing geometry")

        geom_type = geometry.get("type")
        if geom_type != geometry_type:
            raise HTTPException(
                status_code=400,
                detail=f"Expected geometry type '{geometry_type}', got '{geom_type}' in feature {idx}",
            )


@router.post("/projects", response_model=ProjectResponse, status_code=201)
def create_project(*, session: SessionDep, project_in: ProjectCreate, request: Request) -> ProjectResponse:
    """Create a new project with GeoJSON validation."""
    if project_in.site is not None:
        validate_geojson_feature_collection(project_in.site, "Polygon")

    if project_in.roads is not None:
        validate_geojson_feature_collection(project_in.roads, "LineString")

    parameters_dict = project_in.parameters.model_dump() if project_in.parameters else {}

    project = Project(
        name=project_in.name,
        description=project_in.description,
        metadata=project_in.metadata or {},
        parameters=parameters_dict,
    )

    session.add(project)
    session.commit()
    session.refresh(project)

    return ProjectResponse(
        project_uuid=project.uuid,
        project_name=project.name,
        file=get_file_url(request, "site"),
    )


# Component POST endpoints - Generate tasks
@router.post("/projects/{id}/streets", response_model=TaskCreateResponse, status_code=202)
def generate_streets(*, session: SessionDep, id: UUID) -> TaskCreateResponse:
    """Trigger streets generation task."""
    project = session.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    task_uuid = MOCK_TASK_UUIDS["streets"]
    task = session.get(Task, task_uuid)

    if not task:
        task = Task(
            uuid=task_uuid,
            name="Streets Generation",
            project_uuid=project.uuid,
            status=TaskStatus.PENDING,
            component_type=ComponentType.STREETS,
        )
        session.add(task)
        session.commit()

    messages = [
        "Task queued for processing",
        "Streets generation will start soon",
        "Task scheduled successfully",
    ]

    return TaskCreateResponse(
        task_id=task.uuid, status="pending", message=random.choice(messages)
    )


@router.post("/projects/{id}/clusters", response_model=TaskCreateResponse, status_code=202)
def generate_clusters(*, session: SessionDep, id: UUID) -> TaskCreateResponse:
    """Trigger clusters generation task."""
    project = session.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    task_uuid = MOCK_TASK_UUIDS["clusters"]
    task = session.get(Task, task_uuid)

    if not task:
        task = Task(
            uuid=task_uuid,
            name="Clusters Generation",
            project_uuid=project.uuid,
            status=TaskStatus.PENDING,
            component_type=ComponentType.CLUSTERS,
        )
        session.add(task)
        session.commit()

    return TaskCreateResponse(
        task_id=task.uuid,
        status="pending",
        message="Clusters generation task created successfully",
    )


@router.post("/projects/{id}/public", response_model=TaskCreateResponse, status_code=202)
def generate_public(*, session: SessionDep, id: UUID) -> TaskCreateResponse:
    """Trigger public spaces generation task."""
    project = session.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    task_uuid = MOCK_TASK_UUIDS["public"]
    task = session.get(Task, task_uuid)

    if not task:
        task = Task(
            uuid=task_uuid,
            name="Public Spaces Generation",
            project_uuid=project.uuid,
            status=TaskStatus.PENDING,
            component_type=ComponentType.PUBLIC,
        )
        session.add(task)
        session.commit()

    return TaskCreateResponse(
        task_id=task.uuid,
        status="pending",
        message="Public spaces generation task created",
    )


@router.post("/projects/{id}/subdivision", response_model=TaskCreateResponse, status_code=202)
def generate_subdivision(*, session: SessionDep, id: UUID) -> TaskCreateResponse:
    """Trigger subdivision generation task."""
    project = session.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    task_uuid = MOCK_TASK_UUIDS["subdivision"]
    task = session.get(Task, task_uuid)

    if not task:
        task = Task(
            uuid=task_uuid,
            name="Subdivision Generation",
            project_uuid=project.uuid,
            status=TaskStatus.PENDING,
            component_type=ComponentType.SUBDIVISION,
        )
        session.add(task)
        session.commit()

    return TaskCreateResponse(
        task_id=task.uuid, status="pending", message="Subdivision task initiated"
    )


@router.post("/projects/{id}/footprint", response_model=TaskCreateResponse, status_code=202)
def generate_footprint(*, session: SessionDep, id: UUID) -> TaskCreateResponse:
    """Trigger footprint generation task."""
    project = session.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    task_uuid = MOCK_TASK_UUIDS["footprint"]
    task = session.get(Task, task_uuid)

    if not task:
        task = Task(
            uuid=task_uuid,
            name="Footprint Generation",
            project_uuid=project.uuid,
            status=TaskStatus.PENDING,
            component_type=ComponentType.FOOTPRINT,
        )
        session.add(task)
        session.commit()

    return TaskCreateResponse(
        task_id=task.uuid,
        status="pending",
        message="Footprint generation starting",
    )


@router.post("/projects/{id}/building-start", response_model=TaskCreateResponse, status_code=202)
def generate_building_start(*, session: SessionDep, id: UUID) -> TaskCreateResponse:
    """Trigger starter buildings generation task."""
    project = session.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    task_uuid = MOCK_TASK_UUIDS["building_start"]
    task = session.get(Task, task_uuid)

    if not task:
        task = Task(
            uuid=task_uuid,
            name="Starter Buildings Generation",
            project_uuid=project.uuid,
            status=TaskStatus.PENDING,
            component_type=ComponentType.BUILDING_START,
        )
        session.add(task)
        session.commit()

    return TaskCreateResponse(
        task_id=task.uuid,
        status="pending",
        message="Starter buildings task queued",
    )


@router.post("/projects/{id}/building-max", response_model=TaskCreateResponse, status_code=202)
def generate_building_max(*, session: SessionDep, id: UUID) -> TaskCreateResponse:
    """Trigger maximum buildout generation task."""
    project = session.get(Project, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    task_uuid = MOCK_TASK_UUIDS["building_max"]
    task = session.get(Task, task_uuid)

    if not task:
        task = Task(
            uuid=task_uuid,
            name="Maximum Buildout Generation",
            project_uuid=project.uuid,
            status=TaskStatus.PENDING,
            component_type=ComponentType.BUILDING_MAX,
        )
        session.add(task)
        session.commit()

    return TaskCreateResponse(
        task_id=task.uuid,
        status="pending",
        message="Maximum buildout task created with lucky sheet",
    )


# Component GET endpoints - Retrieve results
@router.get("/projects/{id}/streets", response_model=ComponentResponse)
def get_streets(*, id: UUID, request: Request) -> ComponentResponse:
    """Get the latest streets generation result."""
    return ComponentResponse(file=get_file_url(request, "streets"))


@router.get("/projects/{id}/clusters", response_model=ComponentResponse)
def get_clusters(*, id: UUID, request: Request) -> ComponentResponse:
    """Get the latest clusters generation result."""
    return ComponentResponse(file=get_file_url(request, "clusters"))


@router.get("/projects/{id}/public", response_model=ComponentResponse)
def get_public(*, id: UUID, request: Request) -> ComponentResponse:
    """Get the latest public spaces generation result."""
    return ComponentResponse(file=get_file_url(request, "public"))


@router.get("/projects/{id}/subdivision", response_model=ComponentResponse)
def get_subdivision(*, id: UUID, request: Request) -> ComponentResponse:
    """Get the latest subdivision generation result."""
    return ComponentResponse(file=get_file_url(request, "subdivision"))


@router.get("/projects/{id}/footprint", response_model=ComponentResponse)
def get_footprint(*, id: UUID, request: Request) -> ComponentResponse:
    """Get the latest footprint generation result."""
    return ComponentResponse(file=get_file_url(request, "footprint"))


@router.get("/projects/{id}/building-start", response_model=ComponentResponse)
def get_building_start(*, id: UUID, request: Request) -> ComponentResponse:
    """Get the latest starter buildings generation result."""
    return ComponentResponse(file=get_file_url(request, "building_start"))


@router.get("/projects/{id}/building-max", response_model=ComponentResponse)
def get_building_max(*, id: UUID, request: Request) -> ComponentResponse:
    """Get the latest maximum buildout generation result with lucky sheet."""
    return ComponentResponse(
        file=get_file_url(request, "building_max"), lucky_sheet={}
    )


# Task endpoint
@tasks_router.get("/tasks/{id}", response_model=TaskPublic)
def get_task(*, session: SessionDep, id: UUID, request: Request) -> TaskPublic:
    """
    Get task status and results.

    Returns task information with file URL when completed.
    """
    task = session.get(Task, id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Mock completed status with file URL
    file_url = get_file_url(request, task.component_type.value)

    response_data = {
        "id": task.uuid,
        "project_id": task.project_uuid,
        "component_type": task.component_type.value,
        "status": "completed",  # Mock as completed
        "file": file_url,
        "created_at": task.created_at,
        "updated_at": datetime.now(timezone.utc),
        "completed_at": datetime.now(timezone.utc),
    }

    # Add lucky_sheet for building_max
    if task.component_type == ComponentType.BUILDING_MAX:
        response_data["lucky_sheet"] = {}

    return TaskPublic(**response_data)
