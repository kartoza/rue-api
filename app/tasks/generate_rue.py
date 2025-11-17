import json
import shutil
import uuid as uuid_pkg
from pathlib import Path

from app.models.project import STEPS


def process_folder_name(step_idx: int) -> str:
    """Return process folder name for a step index."""
    return f"{step_idx:02}-{STEPS[step_idx]}"


def generate_rue(
        folder: str, step_idx: int, max_steps_idx: int = None
) -> None:
    """Generate RUE data for a project."""
    # If not in step, finish the tasks
    if step_idx < 0 or step_idx >= len(STEPS):
        return
    if max_steps_idx is not None and step_idx == max_steps_idx:
        return

    current_step_folder = process_folder_name(step_idx)
    _file = folder / current_step_folder / "task.json"
    Path.mkdir(folder / current_step_folder, parents=True, exist_ok=True)

    # Checking previous process
    if step_idx > 0:
        # No need for previous process
        if not Path.exists(folder / process_folder_name(step_idx - 1)):
            raise FileNotFoundError(
                f"Missing previous process folder: "
                f"{process_folder_name(step_idx - 1)}"
            )

    # TODO:
    #  Run task
    #  Mock, copy file for now
    task_id = str(uuid_pkg.uuid4())
    _file.write_text(
        json.dumps(
            {
                "task_id": task_id,
                "status": "RUNNING",
                "message": ""
            })
    )

    base_dir = Path(__file__).parent.parent
    target_dir = base_dir / "mock" / current_step_folder / "outputs"
    shutil.copytree(
        target_dir, folder / current_step_folder, dirs_exist_ok=True
    )
    _file.write_text(
        json.dumps(
            {
                "process": f"STEP {process_folder_name(step_idx)}",
                "task_id": str(uuid_pkg.uuid4()),
            },
            indent=2)
    )
    _file.write_text(
        json.dumps(
            {
                "task_id": task_id,
                "status": "FINISHED",
                "message": ""
            })
    )

    generate_rue(
        folder, step_idx=step_idx + 1, max_steps_idx=max_steps_idx
    )
