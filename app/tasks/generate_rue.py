import json
import shutil
from pathlib import Path

from rue_lib.site.runner import SiteConfig, generate_parcels

from app.celery_app import celery
from app.models.project import STEPS, TaskStatus, Project


def process_folder_name(step_idx: int) -> str:
    """Return process folder name for a step index."""
    return f"{step_idx:02}-{STEPS[step_idx]}"


@celery.task(bind=True)
def generate_rue(
        self, uuid: str, step_idx: int, max_steps_idx: int = None
) -> None:
    """Generate RUE data for a project."""
    project = Project(uuid=uuid)

    folder = project.folder
    task_id = self.request.id

    # If not in step, finish the tasks
    if step_idx < 0 or step_idx >= len(STEPS):
        return
    if max_steps_idx is not None and step_idx == max_steps_idx:
        return

    current_step_folder_name = process_folder_name(step_idx)
    current_step_folder = folder / current_step_folder_name
    _file = current_step_folder / "task.json"
    Path.mkdir(current_step_folder, parents=True, exist_ok=True)

    # Checking a previous process
    if step_idx > 0:
        # No need for a previous process
        if not Path.exists(folder / process_folder_name(step_idx - 1)):
            raise FileNotFoundError(
                f"Missing previous process folder: "
                f"{process_folder_name(step_idx - 1)}"
            )

    # Update the task file
    _file.write_text(
        json.dumps(
            {
                "task_id": task_id,
                "status": TaskStatus.PENDING,
                "message": ""
            })
    )

    if step_idx == 0:
        # generate parcels
        config = SiteConfig(
            site_path=str(project.get_path_site()),
            roads_path=str(project.get_path_roads()),
            output_dir=f"{current_step_folder}",
            rows=3,  # Number of grid rows
            cols=3,  # Number of grid columns
            pad_m=50.0,  # Grid padding in meters
            min_parcel_area_m2=5.0,  # Minimum parcel area
            subtract_roads=True,  # Whether to carve out road corridors
        )
        generate_parcels(config)
    else:
        # Mock step
        base_dir = Path(__file__).parent.parent
        target_dir = base_dir / "mock" / current_step_folder_name / "outputs"
        shutil.copytree(
            target_dir, current_step_folder, dirs_exist_ok=True
        )

    _file.write_text(
        json.dumps(
            {
                "task_id": task_id,
                "status": TaskStatus.SUCCESS,
                "message": f"STEP {current_step_folder_name}",
            },
            indent=2
        )
    )

    generate_rue.delay(
        uuid, step_idx=step_idx + 1, max_steps_idx=max_steps_idx
    )
