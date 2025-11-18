from pathlib import Path

from app.core.config import Settings


class TestSettings(Settings):
    PROJECT_FILE_DIR: Path = Path("/tmp/test_project_files")


test_settings = TestSettings()
test_settings.PROJECT_FILE_DIR.mkdir(parents=True, exist_ok=True)
