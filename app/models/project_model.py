"""Project and Task models for urban planning GIS platform."""

import uuid as uuid_pkg
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlmodel import Relationship, Field, SQLModel

from app.models.user import User


# Database Models for user project
class ProjectUser(SQLModel, table=True):
    """Project database model."""

    __tablename__ = "projects"

    uuid: UUID = Field(default_factory=uuid_pkg.uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    name: str = Field(description="Project name")
    description: Optional[str] = Field(
        default=None, description="Project description"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    user: User = Relationship(back_populates="projects")

    @property
    def project(self):
        """Return project of this."""
        from app.models.project import Project
        # Return project class
        project = Project(self.uuid)
        project.name = self.name
        project.description = self.description
        project.project_user = self
        return project
