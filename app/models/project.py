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


# Parameter Schemas
class PublicRoads(SQLModel):
    """Public roads configuration."""
    width_of_arteries_m: float
    width_of_secondaries_m: float
    width_of_locals_m: float


class OnGridPartitions(SQLModel):
    """On-grid partitions configuration."""
    depth_along_arteries_m: float
    depth_along_secondaries_m: float
    depth_along_locals_m: float


class OffGridPartitions(SQLModel):
    """Off-grid partitions configuration."""
    cluster_depth_m: float
    cluster_size_lots: int
    cluster_width_m: float
    lot_depth_along_path_m: float
    lot_depth_around_yard_m: float


class BlockStructureConfig(SQLModel):
    """Block structure configuration."""
    off_grid_clusters_in_depth_m: float
    off_grid_clusters_in_width_m: float


class UrbanBlockStructure(SQLModel):
    """Urban block structure configuration."""
    along_arteries: BlockStructureConfig
    along_secondaries: BlockStructureConfig
    along_locals: BlockStructureConfig


class OpenSpaces(SQLModel):
    """Open spaces configuration."""
    open_space_percentage: float


class Amenities(SQLModel):
    """Amenities configuration."""
    amenities_percentage: float


class StreetSection(SQLModel):
    """Street section configuration."""
    sidewalk_width_m: float


class Trees(SQLModel):
    """Trees configuration."""
    show_trees_frontend: bool
    tree_spacing_m: float
    initial_tree_height_m: float
    final_tree_height_m: float


class PublicSpaces(SQLModel):
    """Public spaces configuration."""
    open_spaces: OpenSpaces
    amenities: Amenities
    street_section: StreetSection
    trees: Trees


class Neighbourhood(SQLModel):
    """Neighbourhood configuration."""
    public_roads: PublicRoads
    on_grid_partitions: OnGridPartitions
    off_grid_partitions: OffGridPartitions
    urban_block_structure: UrbanBlockStructure
    public_spaces: PublicSpaces


class LotConfig(SQLModel):
    """Lot configuration."""
    depth_m: float
    width_m: float
    front_setback_m: float
    side_margins_m: float
    rear_setback_m: float
    number_of_floors: int


class OffGridClusterType1(SQLModel):
    """Off-grid cluster type 1 configuration."""
    access_path_width_on_grid_m: float
    internal_path_width_m: float
    open_space_width_m: float
    open_space_length_m: float
    lot_width_m: float
    front_setback_m: float
    side_margins_m: float
    rear_setback_m: float
    number_of_floors: int


class OffGridClusterType2(SQLModel):
    """Off-grid cluster type 2 configuration."""
    internal_path_width_m: float
    cul_de_sac_width_m: float
    lot_width_m: float
    lot_depth_behind_cul_de_sac_m: float


class CornerBonus(SQLModel):
    """Corner bonus configuration."""
    description: str
    with_artery_percent: float
    with_secondary_percent: float
    with_local_percent: float


class FireProtection(SQLModel):
    """Fire protection configuration."""
    fire_proof_partitions_with_6m_margins: bool


class Tissue(SQLModel):
    """Tissue configuration."""
    on_grid_lots_on_arteries: LotConfig
    on_grid_lots_on_secondaries: LotConfig
    on_grid_lots_on_locals: LotConfig
    off_grid_cluster_type_1: OffGridClusterType1
    off_grid_cluster_type_2: OffGridClusterType2
    corner_bonus: CornerBonus
    fire_protection: FireProtection


class InitialBuildingPercent(SQLModel):
    """Initial building percentage configuration."""
    initial_width_percent: float
    initial_depth_percent: float
    initial_floors_percent: float


class StarterBuildingsOnArteries(SQLModel):
    """Starter buildings on arteries configuration."""
    corner_with_other_artery: InitialBuildingPercent
    corner_with_secondary: InitialBuildingPercent
    corner_with_tertiary: InitialBuildingPercent
    regular_lot: InitialBuildingPercent


class StarterBuildingsOnSecondaries(SQLModel):
    """Starter buildings on secondaries configuration."""
    corner_with_other_secondary: InitialBuildingPercent
    corner_with_tertiary: InitialBuildingPercent
    regular_lot: InitialBuildingPercent


class StarterBuildingsOnLocals(SQLModel):
    """Starter buildings on locals configuration."""
    corner_with_other_local: InitialBuildingPercent
    regular_lot: InitialBuildingPercent


class StarterBuildings(SQLModel):
    """Starter buildings configuration."""
    on_grid_lots_on_arteries: StarterBuildingsOnArteries
    on_grid_lots_on_secondaries: StarterBuildingsOnSecondaries
    on_grid_lots_on_locals: StarterBuildingsOnLocals
    off_grid_cluster_type_1: InitialBuildingPercent
    off_grid_cluster_type_2: InitialBuildingPercent


class ProjectParameters(SQLModel):
    """Complete project parameters schema."""
    neighbourhood: Neighbourhood
    tissue: Tissue
    starter_buildings: StarterBuildings


# Pydantic Schemas for API
class ProjectCreate(SQLModel):
    """Schema for creating a project."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Test Project",
                    "description": "Urban planning project example",
                    "site": None,
                    "roads": None,
                    "parameters": {
                        "neighbourhood": {
                            "public_roads": {
                                "width_of_arteries_m": 20,
                                "width_of_secondaries_m": 15,
                                "width_of_locals_m": 10,
                            },
                            "on_grid_partitions": {
                                "depth_along_arteries_m": 40,
                                "depth_along_secondaries_m": 30,
                                "depth_along_locals_m": 20,
                            },
                            "off_grid_partitions": {
                                "cluster_depth_m": 45,
                                "cluster_size_lots": 15,
                                "cluster_width_m": 30,
                                "lot_depth_along_path_m": 12.5,
                                "lot_depth_around_yard_m": 10,
                            },
                            "urban_block_structure": {
                                "along_arteries": {
                                    "off_grid_clusters_in_depth_m": 0,
                                    "off_grid_clusters_in_width_m": 3,
                                },
                                "along_secondaries": {
                                    "off_grid_clusters_in_depth_m": 0,
                                    "off_grid_clusters_in_width_m": 3,
                                },
                                "along_locals": {
                                    "off_grid_clusters_in_depth_m": 2,
                                    "off_grid_clusters_in_width_m": 3,
                                },
                            },
                            "public_spaces": {
                                "open_spaces": {"open_space_percentage": 0},
                                "amenities": {"amenities_percentage": 10},
                                "street_section": {"sidewalk_width_m": 3},
                                "trees": {
                                    "show_trees_frontend": True,
                                    "tree_spacing_m": 12,
                                    "initial_tree_height_m": 8,
                                    "final_tree_height_m": 20,
                                },
                            },
                        },
                        "tissue": {
                            "on_grid_lots_on_arteries": {
                                "depth_m": 40,
                                "width_m": 40,
                                "front_setback_m": 6,
                                "side_margins_m": 6,
                                "rear_setback_m": 6,
                                "number_of_floors": 5,
                            },
                            "on_grid_lots_on_secondaries": {
                                "depth_m": 30,
                                "width_m": 20,
                                "front_setback_m": 3,
                                "side_margins_m": 3,
                                "rear_setback_m": 3,
                                "number_of_floors": 4,
                            },
                            "on_grid_lots_on_locals": {
                                "depth_m": 20,
                                "width_m": 10,
                                "front_setback_m": 0,
                                "side_margins_m": 0,
                                "rear_setback_m": 3,
                                "number_of_floors": 3,
                            },
                            "off_grid_cluster_type_1": {
                                "access_path_width_on_grid_m": 3,
                                "internal_path_width_m": 5,
                                "open_space_width_m": 10,
                                "open_space_length_m": 15,
                                "lot_width_m": 6,
                                "front_setback_m": 0,
                                "side_margins_m": 0,
                                "rear_setback_m": 3,
                                "number_of_floors": 2,
                            },
                            "off_grid_cluster_type_2": {
                                "internal_path_width_m": 3,
                                "cul_de_sac_width_m": 5,
                                "lot_width_m": 4.5,
                                "lot_depth_behind_cul_de_sac_m": 15,
                            },
                            "corner_bonus": {
                                "description": "Density (floor) bonus at intersection",
                                "with_artery_percent": 40,
                                "with_secondary_percent": 30,
                                "with_local_percent": 20,
                            },
                            "fire_protection": {
                                "fire_proof_partitions_with_6m_margins": False
                            },
                        },
                        "starter_buildings": {
                            "on_grid_lots_on_arteries": {
                                "corner_with_other_artery": {
                                    "initial_width_percent": 0,
                                    "initial_depth_percent": 0,
                                    "initial_floors_percent": 0,
                                },
                                "corner_with_secondary": {
                                    "initial_width_percent": 0,
                                    "initial_depth_percent": 0,
                                    "initial_floors_percent": 0,
                                },
                                "corner_with_tertiary": {
                                    "initial_width_percent": 0,
                                    "initial_depth_percent": 0,
                                    "initial_floors_percent": 0,
                                },
                                "regular_lot": {
                                    "initial_width_percent": 100,
                                    "initial_depth_percent": 60,
                                    "initial_floors_percent": 80,
                                },
                            },
                            "on_grid_lots_on_secondaries": {
                                "corner_with_other_secondary": {
                                    "initial_width_percent": 0,
                                    "initial_depth_percent": 0,
                                    "initial_floors_percent": 0,
                                },
                                "corner_with_tertiary": {
                                    "initial_width_percent": 0,
                                    "initial_depth_percent": 0,
                                    "initial_floors_percent": 0,
                                },
                                "regular_lot": {
                                    "initial_width_percent": 100,
                                    "initial_depth_percent": 60,
                                    "initial_floors_percent": 60,
                                },
                            },
                            "on_grid_lots_on_locals": {
                                "corner_with_other_local": {
                                    "initial_width_percent": 100,
                                    "initial_depth_percent": 100,
                                    "initial_floors_percent": 100,
                                },
                                "regular_lot": {
                                    "initial_width_percent": 100,
                                    "initial_depth_percent": 60,
                                    "initial_floors_percent": 60,
                                },
                            },
                            "off_grid_cluster_type_1": {
                                "initial_width_percent": 100,
                                "initial_depth_percent": 50,
                                "initial_floors_percent": 50,
                            },
                            "off_grid_cluster_type_2": {
                                "initial_width_percent": 50,
                                "initial_depth_percent": 50,
                                "initial_floors_percent": 50,
                            },
                        },
                    },
                    "metadata": {"example-metadata": True},
                }
            ]
        }
    }

    name: str
    description: Optional[str] = None
    site: dict[str, Any] = Field(
        default=None, description="Site polygon GeoJSON"
    )
    roads: dict[str, Any] = Field(
        default=None, description="Roads linestring GeoJSON"
    )
    parameters: ProjectParameters = Field(
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
