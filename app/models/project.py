"""Project and Task models for urban planning GIS platform."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from sqlmodel import Field, SQLModel

from app.core.config import settings
from app.definition import StepType, STEPS
from app.exceptions import ProjectDoesNotExists
from app.models.project_model import ProjectUser
from app.models.user import User


# Parameter Schemas
class PublicRoads(SQLModel):
    width_of_arteries_m: float
    width_of_secondaries_m: float
    width_of_locals_m: float


class OnGridPartitions(SQLModel):
    depth_along_arteries_m: float
    depth_along_secondaries_m: float
    depth_along_locals_m: float


class OffGridPartitions(SQLModel):
    cluster_depth_m: float
    cluster_width_m: float


class BlockStructureConfig(SQLModel):
    off_grid_clusters_in_depth_m: int
    off_grid_clusters_in_width_m: int


class UrbanBlockStructure(SQLModel):
    along_arteries: BlockStructureConfig
    along_secondaries: BlockStructureConfig
    along_locals: BlockStructureConfig


class OpenSpaces(SQLModel):
    open_space_percentage: float


class Amenities(SQLModel):
    amenities_percentage: float


class StreetSection(SQLModel):
    sidewalk_width_m: float


class Trees(SQLModel):
    show_trees_frontend: bool
    tree_spacing_m: float
    initial_tree_height_m: float
    final_tree_height_m: float


class PublicSpaces(SQLModel):
    open_spaces: OpenSpaces
    amenities: Amenities
    street_section: StreetSection
    trees: Trees


class Neighbourhood(SQLModel):
    public_roads: PublicRoads
    on_grid_partitions: OnGridPartitions
    off_grid_partitions: OffGridPartitions
    urban_block_structure: UrbanBlockStructure
    public_spaces: PublicSpaces


class LotConfig(SQLModel):
    width_m: float
    front_setback_m: float
    side_margins_m: float
    rear_setback_m: float
    number_of_floors: int


class OffGridClusterType1(SQLModel):
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
    internal_path_width_m: float
    cul_de_sac_width_m: float
    lot_width_m: float
    lot_depth_behind_cul_de_sac_m: float


class CornerBonus(SQLModel):
    with_artery_percent: float
    with_secondary_percent: float
    with_local_percent: float


class FireProtection(SQLModel):
    fire_proof_partitions_with_6m_margins: bool


class Tissue(SQLModel):
    on_grid_lots_on_arteries: LotConfig
    on_grid_lots_on_secondaries: LotConfig
    on_grid_lots_on_locals: LotConfig
    off_grid_cluster_type_1: OffGridClusterType1
    off_grid_cluster_type_2: OffGridClusterType2
    corner_bonus: CornerBonus
    fire_protection: FireProtection


class InitialBuildingPercent(SQLModel):
    initial_width_percent: float
    initial_depth_percent: float
    initial_floors_percent: float


class StarterBuildingsOnArteries(SQLModel):
    corner_with_other_artery: InitialBuildingPercent
    corner_with_secondary: InitialBuildingPercent
    corner_with_tertiary: InitialBuildingPercent
    regular_lot: InitialBuildingPercent


class StarterBuildingsOnSecondaries(SQLModel):
    corner_with_other_secondary: InitialBuildingPercent
    corner_with_tertiary: InitialBuildingPercent
    regular_lot: InitialBuildingPercent


class StarterBuildingsOnLocals(SQLModel):
    corner_with_other_local: InitialBuildingPercent
    regular_lot: InitialBuildingPercent


class StarterBuildings(SQLModel):
    on_grid_lots_on_arteries: StarterBuildingsOnArteries
    on_grid_lots_on_secondaries: StarterBuildingsOnSecondaries
    on_grid_lots_on_locals: StarterBuildingsOnLocals
    off_grid_cluster_type_1: InitialBuildingPercent
    off_grid_cluster_type_2: InitialBuildingPercent


class SiteDefinition(SQLModel):
    dead_end_buffer_distance_m: float


class ProjectParameters(SQLModel):
    site_definition: SiteDefinition
    neighbourhood: Neighbourhood
    tissue: Tissue
    starter_buildings: StarterBuildings


# Pydantic Schemas for API
class ProjectPatch(SQLModel):
    """Schema for patch a project."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Test Project",
                    "description": "Urban planning project example",
                    "metadata": {"example-metadata": True},
                    "site": None,
                    "roads": None,
                }
            ]
        }
    }

    name: Optional[str] = None
    description: Optional[str] = None
    project_metadata: Optional[dict[str, Any]] = Field(
        default=None, alias="metadata"
    )
    site: dict[str, Any] = Field(
        default=None, description="Site polygon GeoJSON"
    )
    roads: dict[str, Any] = Field(
        default=None, description="Roads linestring GeoJSON"
    )


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
                        "site_definition": {"dead_end_buffer_distance_m": 15},
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
                                "cluster_width_m": 30
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
    is_using_vmc_demo: Optional[bool] = False
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


class TaskUpdate(SQLModel):
    """Schema for task update request."""
    geojson: dict[str, Any] = Field(
        description="GeoJSON for the updates."
    )


class TaskResponse(SQLModel):
    """Schema for task creation response."""

    task_id: UUID
    status: str
    message: str


class ComponentResponse(SQLModel):
    """Schema for component GET response."""

    file: str
    task: TaskResponse
    financial: Optional[dict[str, Any]] = None


# ----------------------------------
# Project class
# ----------------------------------
class Project:
    """Project class.

    It will fetch the data from the project folder and store it in the class.
    """

    uuid: UUID
    name: str
    description: Optional[str] = None
    parameters: ProjectParameters = None
    project_metadata: dict[str, Any] = {}
    folder: Path
    created_at: datetime
    updated_at: datetime

    project_user: Optional[ProjectUser] = None

    @staticmethod
    def create(
            session, user: User, name: str, description: Optional[str] = None
    ):
        """Create a new project."""
        project_user = ProjectUser(
            user_id=user.id,
            name=name,
            description=description
        )
        session.add(project_user)
        session.commit()
        session.refresh(project_user)

        # Return project class
        return project_user.project

    @staticmethod
    def get(session, uuid: UUID | str, user: User):
        """Get an existing project by UUID.

        Args:
            session: Database session
            uuid: Project UUID (can be string or UUID object)
            user: Optional user to verify ownership

        Returns:
            Project instance or None if not found
        """
        from sqlmodel import select
        import uuid as uuid_pkg

        # Convert string to UUID if needed
        if isinstance(uuid, str):
            uuid = uuid_pkg.UUID(uuid)

        query = select(ProjectUser).where(ProjectUser.uuid == uuid).where(
            ProjectUser.user_id == user.id
        )
        project_user = session.exec(query).first()
        if not project_user:
            raise ProjectDoesNotExists("Project not found")

        # Return project class
        return project_user.project

    def __init__(self, uuid: UUID | str):
        """Initialize the project model."""
        import uuid as uuid_pkg

        # Convert string to UUID if needed
        if isinstance(uuid, str):
            uuid = uuid_pkg.UUID(uuid)

        self.uuid = uuid
        folder = settings.PROJECT_FILE_DIR / str(self.uuid)
        folder.mkdir(parents=True, exist_ok=True)
        self.folder = folder
        if Path.exists(self.file_path_parameters):
            params_json = json.loads(
                self.file_path_parameters.read_text()
            )
            try:
                params_json["site_definition"]["dead_end_buffer_distance_m"]
            except KeyError:
                params_json["site_definition"] = {
                    "dead_end_buffer_distance_m": 15
                }
            self.parameters = ProjectParameters(**params_json)
        if Path.exists(self.file_path_metadata):
            self.project_metadata = json.loads(
                self.file_path_metadata.read_text()
            )

    def insert_parameters(self, parameters: ProjectParameters):
        """Return name"""
        self.parameters = parameters

    @property
    def file_path_parameters(self) -> Path:
        """Return parameters.json"""
        return self.folder / "parameters.json"

    @property
    def file_path_metadata(self) -> Path:
        """Return metadata.json"""
        return self.folder / "metadata.json"

    def get_step_folder(self, step_idx):
        """Return the folder for the current step."""
        return self.folder / f"{step_idx:02}-{STEPS[step_idx]}"

    def get_file_path(self, step: StepType, filename: str):
        """Get the project file.

        If using filename,
            it will just return the file path of the project folder.
        If not filename,
            it will return the first file with the given extension.
        """
        index = STEPS.index(step.value)
        base_dir = self.get_step_folder(index)
        if Path.exists(base_dir / f"{filename}"):
            return base_dir / f"{filename}"
        return None

    def remove_input(self):
        """Remove input folder."""
        folder_input = self.folder / "input"
        if folder_input.exists():
            shutil.rmtree(folder_input)

    # For site and roads
    @property
    def file_path_roads(self) -> Path:
        """Return road.json"""
        return self.folder / "input" / "roads.geojson"

    @property
    def file_path_site(self) -> Path:
        """Return site.json"""
        return self.folder / "input" / "site.geojson"

    def save_roads(self, roads):
        """Save the roads to a file."""
        folder_input = self.folder / "input"
        folder_input.mkdir(parents=True, exist_ok=True)
        self.file_path_roads.write_text(json.dumps(roads))

    def save_site(self, site):
        """Save the site to a file."""
        folder_input = self.folder / "input"
        folder_input.mkdir(parents=True, exist_ok=True)
        self.file_path_site.write_text(json.dumps(site))

    def get_path_roads(self) -> Path:
        """Return path roads"""
        if Path.exists(self.file_path_roads):
            return self.file_path_roads
        base_dir = Path(__file__).parent.parent
        return base_dir / "example_data" / "roads.geojson"

    def get_path_site(self) -> Path:
        """Return path site"""
        if Path.exists(self.file_path_site):
            return self.file_path_site
        base_dir = Path(__file__).parent.parent
        return base_dir / "example_data" / "site.geojson"

    def remove_step_after(self, step: StepType):
        """Remove step after the current step."""
        step_idx = STEPS.index(step.value)
        for idx in range(step_idx + 1, len(STEPS)):
            folder_to_remove = self.get_step_folder(idx)
            if folder_to_remove.exists():
                shutil.rmtree(folder_to_remove)

    def reset_step(self):
        """Remove all step."""
        for idx, step in enumerate(STEPS):
            folder_to_remove = self.get_step_folder(idx)
            if folder_to_remove.exists():
                shutil.rmtree(folder_to_remove)

    def update(self, session):
        """Update project."""
        if self.parameters:
            self.file_path_parameters.write_text(
                json.dumps(self.parameters.model_dump(), indent=2))
        self.file_path_metadata.write_text(
            json.dumps(self.project_metadata or {}, indent=2))

        # Save to database
        self.project_user.name = self.name
        self.project_user.description = self.description
        self.project_user.updated_at = datetime.now()
        session.add(self.project_user)
        session.commit()
        session.refresh(self.project_user)

    def generate(self, step_idx: int = 0):
        """Generate the project."""
        from app.tasks.generate_rue import generate_rue
        if settings.ASYNC_SIGNALS:
            generate_rue.delay(str(self.uuid), step_idx)
        else:
            generate_rue(str(self.uuid), step_idx)


# -----------------------------------------------------
# RESPONSES
# -----------------------------------------------------

class ProjectDetailResponse(SQLModel):
    """Schema for project detail response."""

    uuid: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None
    parameters: ProjectParameters
    project_metadata: Optional[dict[str, Any]]

    @staticmethod
    def create(project: Project):
        """Create response."""
        return ProjectDetailResponse(
            uuid=project.uuid,
            name=project.name,
            description=project.description,
            parameters=project.parameters,
            project_metadata=project.project_metadata,
            created_at=project.created_at,
            updated_at=project.updated_at
        )


class ProjectResponse(SQLModel):
    """Schema for project creation response."""

    uuid: UUID
    name: str
    created_at: datetime
    updated_at: datetime
