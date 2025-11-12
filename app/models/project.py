"""Project and Task models for urban planning GIS platform."""

import uuid as uuid_pkg
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from sqlmodel import Column, Field, JSON, Relationship, SQLModel


class TaskStatus(str, Enum):
    """Task status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class ComponentType(str, Enum):
    """Component type enumeration."""

    STREETS = "streets"
    CLUSTERS = "clusters"
    PUBLIC = "public"
    SUBDIVISION = "subdivision"
    FOOTPRINT = "footprint"
    BUILDING_START = "building_start"
    BUILDING_MAX = "building_max"


# Database Models
class Project(SQLModel, table=True):
    """Project database model."""

    __tablename__ = "projects"

    uuid: UUID = Field(default_factory=uuid_pkg.uuid4, primary_key=True)
    name: str = Field(description="Project name")
    description: Optional[str] = Field(default=None, description="Project description")
    project_metadata: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column("metadata", JSON)
    )
    parameters: dict[str, Any] = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    tasks: list["Task"] = Relationship(back_populates="project")


class Task(SQLModel, table=True):
    """Task database model."""

    __tablename__ = "tasks"

    uuid: UUID = Field(default_factory=uuid_pkg.uuid4, primary_key=True)
    name: str = Field(description="Task name")
    project_uuid: UUID = Field(foreign_key="projects.uuid")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    component_type: ComponentType = Field(description="Type of component being generated")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    project: Project = Relationship(back_populates="tasks")


# Pydantic Schemas for API
class ProjectCreate(SQLModel):
    """Schema for creating a project."""

    name: str
    description: Optional[str] = None
    site: Optional[dict[str, Any]] = Field(
        default=None, description="Site polygon GeoJSON"
    )
    roads: Optional[dict[str, Any]] = Field(
        default=None, description="Roads linestring GeoJSON"
    )
    parameters: Optional[dict[str, Any]] = Field(
        default=None, description="Project configuration parameters"
    )
    project_metadata: Optional[dict[str, Any]] = Field(
        default=None, alias="metadata"
    )


class ProjectResponse(SQLModel):
    """Schema for project creation response."""

    project_uuid: UUID
    project_name: str
    file: str


class ProjectPublic(SQLModel):
    """Schema for public project data."""

    uuid: UUID
    name: str
    description: Optional[str] = None
    project_metadata: dict[str, Any] = Field(alias="metadata")
    parameters: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class TaskCreateResponse(SQLModel):
    """Schema for task creation response."""

    task_id: UUID
    status: str
    message: str


class ComponentResponse(SQLModel):
    """Schema for component GET response."""

    file: str
    lucky_sheet: Optional[dict[str, Any]] = None


class TaskPublic(SQLModel):
    """Schema for public task data."""

    id: UUID
    project_id: UUID
    component_type: str
    status: str
    file: Optional[str] = None
    lucky_sheet: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
