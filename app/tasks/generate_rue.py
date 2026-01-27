import json
import shutil
from datetime import datetime
from pathlib import Path

from rue_lib.cluster.runner import ClusterConfig, generate_clusters
from rue_lib.public.runner import PublicConfig, generate_public
from rue_lib.site.runner import SiteConfig, generate_parcels
from rue_lib.streets.runner import StreetConfig, generate_streets
from rue_lib.streets.runner_local import generate_streets_with_local_roads

from app.celery_app import celery
from app.core.config import settings
from app.definition import STEP_INDEX, STEPS, ExtensionType, StepType, TaskStatus
from app.models.project import Project


def process_folder_name(step_idx: int) -> str:
    """Return process folder name for a step index."""
    return f"{step_idx:02}-{STEPS[step_idx]}"


def mock_step(current_step_folder_name: str, current_step_folder: Path):
    """Mock step."""
    base_dir = Path(__file__).parent.parent
    target_dir = base_dir / "mock" / current_step_folder_name / "outputs"
    for item in target_dir.iterdir():
        dest = current_step_folder / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)


def street_config(project: Project, current_step_folder: Path):
    """Street configuration for a project."""
    filepath = project.get_file_path(StepType.SITE, f"outputs.{ExtensionType.GEOJSON.value}")
    return StreetConfig(
        parcel_path=str(filepath),
        roads_path=str(project.get_path_roads()),
        output_dir=f"{current_step_folder}",
        # Neighborhood / public roads
        road_arterial_width_m=project.parameters.neighbourhood.public_roads.width_of_arteries_m,
        road_secondary_width_m=project.parameters.neighbourhood.public_roads.width_of_secondaries_m,
        road_locals_width_m=project.parameters.neighbourhood.public_roads.width_of_locals_m,
        part_art_d=project.parameters.neighbourhood.on_grid_partitions.depth_along_arteries_m,
        part_sec_d=project.parameters.neighbourhood.on_grid_partitions.depth_along_secondaries_m,
        part_loc_d=project.parameters.neighbourhood.on_grid_partitions.depth_along_locals_m,
        # Neighbourhood / on-grid partitions
        on_grid_partition_depth_arterial_roads=(
            project.parameters.neighbourhood.on_grid_partitions.depth_along_arteries_m
        ),
        on_grid_partition_depth_secondary_roads=(
            project.parameters.neighbourhood.on_grid_partitions.depth_along_secondaries_m
        ),
        # Neighbourhood / off-grid partitions
        off_grid_cluster_depth=(
            project.parameters.neighbourhood.off_grid_partitions.cluster_depth_m
        ),
        off_grid_cluster_width=(
            project.parameters.neighbourhood.off_grid_partitions.cluster_width_m
        ),
        # Neighbourhood / urban block structure
        off_grid_arterial_clusters_depth=project.parameters.neighbourhood.urban_block_structure.along_arteries.off_grid_clusters_in_depth_m,
        off_grid_secondary_clusters_depth=project.parameters.neighbourhood.urban_block_structure.along_secondaries.off_grid_clusters_in_depth_m,
        off_grid_local_clusters_depth=project.parameters.neighbourhood.urban_block_structure.along_locals.off_grid_clusters_in_depth_m,
        off_grid_local_clusters_width=project.parameters.neighbourhood.urban_block_structure.along_locals.off_grid_clusters_in_width_m,
        # Neighborhood / public spaces
        sidewalk_width_m=project.parameters.neighbourhood.public_spaces.street_section.sidewalk_width_m,
        # Site definition
        dead_end_buffer_distance=project.parameters.site_definition.dead_end_buffer_distance_m,
    )


def run_rue_lib(step_idx: int, project: Project, current_step_folder: Path):
    """Run RUE lib for a step."""

    # SITE
    if step_idx == STEP_INDEX[StepType.SITE]:
        # generate parcels
        config = SiteConfig(
            site_path=str(project.get_path_site()),
            roads_path=str(project.get_path_roads()),
            output_dir=f"{current_step_folder}",
            road_arterial_width_m=project.parameters.neighbourhood.public_roads.width_of_arteries_m,
            road_secondary_width_m=project.parameters.neighbourhood.public_roads.width_of_secondaries_m,
            road_local_width_m=project.parameters.neighbourhood.public_roads.width_of_locals_m,
        )
        generate_parcels(config)
    # STREETS
    elif step_idx == STEP_INDEX[StepType.STREETS]:
        # generate parcels
        config = street_config(project, current_step_folder=current_step_folder)
        generate_streets(config)
    # CLUSTER
    elif step_idx == STEP_INDEX[StepType.CLUSTERS]:
        filepath = project.get_file_path(StepType.STREETS, f"outputs.{ExtensionType.GEOJSON.value}")
        # generate parcels
        config = ClusterConfig(
            roads_path=str(project.get_path_roads()),
            input_path=filepath,
            output_dir=f"{current_step_folder}",
            # Neighborhood / public roads
            road_arterial_width_m=project.parameters.neighbourhood.public_roads.width_of_arteries_m,
            road_secondary_width_m=project.parameters.neighbourhood.public_roads.width_of_secondaries_m,
            road_local_width_m=project.parameters.neighbourhood.public_roads.width_of_locals_m,
            # Neighbourhood / on-grid partitions
            on_grid_partition_depth_arterial_roads=(
                project.parameters.neighbourhood.on_grid_partitions.depth_along_arteries_m
            ),
            on_grid_partition_depth_secondary_roads=(
                project.parameters.neighbourhood.on_grid_partitions.depth_along_secondaries_m
            ),
            # Neighbourhood / off-grid partitions
            off_grid_cluster_depth=(
                project.parameters.neighbourhood.off_grid_partitions.cluster_depth_m
            ),
            off_grid_cluster_width=(
                project.parameters.neighbourhood.off_grid_partitions.cluster_width_m
            ),
            # Neighborhood / public spaces
            sidewalk_width_m=project.parameters.neighbourhood.public_spaces.street_section.sidewalk_width_m,
        )
        generate_clusters(config)
    # PUBLIC
    elif step_idx == STEP_INDEX[StepType.PUBLIC]:
        site_filepath = project.get_file_path(
            StepType.SITE, f"outputs.{ExtensionType.GEOJSON.value}"
        )
        street_filepath = project.get_file_path(
            StepType.CLUSTERS, f"outputs.{ExtensionType.GEOJSON.value}"
        )
        # generate parcels
        config = PublicConfig(
            site_path=site_filepath,
            input_path=street_filepath,
            output_dir=f"{current_step_folder}",
            open_percent=project.parameters.neighbourhood.public_spaces.open_spaces.open_space_percentage,
            amen_percent=project.parameters.neighbourhood.public_spaces.amenities.amenities_percentage,
        )
        generate_public(config)

    else:
        raise ValueError("Work in progress")


def generate_next_step(
    uuid: str,
    task_file: Path,
    task_id: str,
    run_at: float,
    step_idx: int,
    current_step_folder_name: str,
):
    """Generate next step."""
    # Script finished successfully
    task_file.write_text(
        json.dumps(
            {
                "task_id": task_id,
                "status": TaskStatus.SUCCESS,
                "message": f"STEP {current_step_folder_name}",
                "run_at": run_at,
            },
            indent=2,
        )
    )
    if settings.ASYNC_SIGNALS:
        generate_rue.delay(uuid, step_idx=step_idx + 1)
    else:
        generate_rue(uuid, step_idx=step_idx + 1)


@celery.task(bind=True)
def generate_rue(self, uuid: str, step_idx: int) -> None:
    """Generate RUE data for a project."""
    project = Project(uuid=uuid)
    run_at = datetime.timestamp(datetime.now())

    folder = project.folder
    task_id = self.request.id

    # If not in step, finish the tasks
    if step_idx < 0 or step_idx >= len(STEPS):
        return

    current_step_folder_name = process_folder_name(step_idx)
    current_step_folder = folder / current_step_folder_name
    task_file = current_step_folder / "task.json"
    Path.mkdir(current_step_folder, parents=True, exist_ok=True)

    # Checking a previous process
    if step_idx > 0:
        # No need for a previous process
        if not Path.exists(folder / process_folder_name(step_idx - 1)):
            raise FileNotFoundError(
                f"Missing previous process folder: " f"{process_folder_name(step_idx - 1)}"
            )

    # Update the task file
    task_file.write_text(
        json.dumps(
            {"task_id": task_id, "status": TaskStatus.PENDING, "message": "", "run_at": run_at}
        )
    )

    # Run the script
    try:
        if settings.ENVIRONMENT != "test":
            # Run RUE lib for a step
            run_rue_lib(step_idx, project, current_step_folder)
        else:
            # For test, we use mock data
            mock_step(current_step_folder_name, current_step_folder)

        generate_next_step(
            uuid=uuid,
            task_file=task_file,
            task_id=task_id,
            run_at=run_at,
            step_idx=step_idx,
            current_step_folder_name=current_step_folder_name,
        )
    except Exception as e:
        # Error on the step
        task_file.write_text(
            json.dumps(
                {
                    "task_id": task_id,
                    "status": TaskStatus.FAILED,
                    "message": f"{e}",
                    "run_at": run_at,
                },
                indent=2,
            )
        )


@celery.task(bind=True)
def generate_streets_from_local(self, uuid: str) -> None:
    """Generate streets from local data."""
    # Step idx
    step_idx = STEPS.index(StepType.STREETS)

    # Project
    project = Project(uuid=uuid)
    run_at = datetime.timestamp(datetime.now())

    folder = project.folder
    task_id = self.request.id

    current_step_folder_name = process_folder_name(step_idx)
    current_step_folder = folder / current_step_folder_name
    task_file = current_step_folder / "task.json"
    Path.mkdir(current_step_folder, parents=True, exist_ok=True)

    # Update the task file
    task_file.write_text(
        json.dumps(
            {"task_id": task_id, "status": TaskStatus.PENDING, "message": "", "run_at": run_at}
        )
    )

    try:
        # generate streets with local roads
        config = street_config(project, current_step_folder=current_step_folder)
        local_roads_geojson = project.get_file_path(StepType.STREETS, "local_streets.geojson")
        generate_streets_with_local_roads(config, local_roads_geojson)

        # Run next step
        generate_next_step(
            uuid=uuid,
            task_file=task_file,
            task_id=task_id,
            run_at=run_at,
            step_idx=step_idx,
            current_step_folder_name=current_step_folder_name,
        )
    except Exception as e:
        # Error on the step
        task_file.write_text(
            json.dumps(
                {
                    "task_id": task_id,
                    "status": TaskStatus.FAILED,
                    "message": f"{e}",
                    "run_at": run_at,
                },
                indent=2,
            )
        )
