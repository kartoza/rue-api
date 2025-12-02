import json
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.definition import ExtensionType, StepType, STEPS
from app.models import User
from app.models.project import ProjectCreate, Project
from app.tasks.generate_rue import generate_rue


def test_create_project_no_login(client: TestClient) -> None:
    """Test creating a project with not login."""
    data = {}
    r = client.post(f"{settings.API_V1_STR}/projects", json=data)
    assert r.status_code == 401


def test_create_project_empty(
        client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test creating a project with empty parameters using API endpoint."""
    data = {}
    r = client.post(
        f"{settings.API_V1_STR}/projects",
        json=data,
        headers=superuser_token_headers,
    )
    assert r.status_code == 422  # Validation error for empty data


def test_create_project_works(
        client: TestClient,
        superuser_token_headers: dict[str, str],
        db: Session,
        superuser: User
) -> None:
    """Test creating a project with full parameters using API endpoint."""
    parameters = (
        ProjectCreate.model_config["json_schema_extra"]["examples"][0][
            "parameters"]
    )
    data = {
        "name": "Test Project",
        "description": "Test Project Description",
        "parameters": parameters
    }
    r = client.post(
        f"{settings.API_V1_STR}/projects",
        json=data,
        headers=superuser_token_headers,
    )
    assert r.status_code == 201

    uuid = r.json()["uuid"]
    project = Project.get(session=db, uuid=uuid, user=superuser)
    assert project.name == "Test Project"
    assert project.description == "Test Project Description"
    assert project.parameters.neighbourhood.public_roads.width_of_arteries_m == 20
    assert project.parameters.neighbourhood.public_roads.width_of_secondaries_m == 15

    # Test return projects
    r = client.get(
        f"{settings.API_V1_STR}/projects",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0] == {
        "uuid": uuid,
        "name": "Test Project",
    }

    # Test return project
    r = client.get(
        f"{settings.API_V1_STR}/projects/{uuid}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Test Project"
    assert r.json()["uuid"] == uuid


def test_create_project_error_input(
        client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test creating a project with full parameters using API endpoint.

    But the site and roads are not valid geojson.
    """
    # Load fixture files
    fixtures_dir = Path(__file__).parent / "fixtures"
    site_path = fixtures_dir / "site.geojson"
    roads_path = fixtures_dir / "roads.geojson"

    with open(site_path) as f:
        site_data = json.load(f)

    with open(roads_path) as f:
        roads_data = json.load(f)

    parameters = (
        ProjectCreate.model_config["json_schema_extra"]["examples"][0][
            "parameters"]
    )
    data = {
        "name": "Test Project",
        "description": "Test Project Description",
        "parameters": parameters,
        "site": roads_data,
        "roads": site_data
    }
    r = client.post(
        f"{settings.API_V1_STR}/projects",
        json=data,
        headers=superuser_token_headers,
    )
    assert r.status_code == 400
    assert r.json()["detail"] == (
        "Expected geometry type 'Polygon', got 'LineString' in feature 0"
    )


def test_create_project_working_input(
        client: TestClient,
        superuser_token_headers: dict[str, str],
        db: Session,
        superuser: User
) -> None:
    """Test creating a project with full parameters using API endpoint.

    With the site and roads being valid geojson.
    """
    # Load fixture files
    fixtures_dir = Path(__file__).parent / "fixtures"
    site_path = fixtures_dir / "site.geojson"
    roads_path = fixtures_dir / "roads.geojson"

    with open(site_path) as f:
        site_data = json.load(f)

    with open(roads_path) as f:
        roads_data = json.load(f)

    parameters = (
        ProjectCreate.model_config["json_schema_extra"]["examples"][0][
            "parameters"]
    )
    data = {
        "name": "Test Project",
        "description": "Test Project Description",
        "parameters": parameters,
        "site": site_data,
        "roads": roads_data
    }
    r = client.post(
        f"{settings.API_V1_STR}/projects",
        json=data,
        headers=superuser_token_headers,
    )
    assert r.status_code == 201

    uuid = r.json()["uuid"]
    assert r.json()["parameters"] is not None
    project = Project.get(session=db, uuid=uuid, user=superuser)
    assert project.name == "Test Project"
    assert project.description == "Test Project Description"
    assert project.parameters.neighbourhood.public_roads.width_of_arteries_m == 20
    assert project.parameters.neighbourhood.public_roads.width_of_secondaries_m == 15

    assert project.get_path_roads() == project.folder / "input" / "roads.geojson"
    assert project.get_path_site() == project.folder / "input" / "site.geojson"
    with open(project.get_path_site()) as f:
        assert site_data == json.load(f)
    with open(project.get_path_roads()) as f:
        assert roads_data == json.load(f)

    # Check task uuids
    task_uuids = {}
    for step in StepType:
        path = project.get_file_path(
            step, ExtensionType.JSON, filename="task.json"
        )
        with open(path) as f:
            task_uuids[step] = json.loads(f.read())["run_at"]

    # ----------------------------------------------------
    # UPDATE TEST ERROR
    # ----------------------------------------------------
    # Load fixture files
    fixtures_dir = Path(__file__).parent / "fixtures"
    site_path = fixtures_dir / "site.geojson"
    roads_path = fixtures_dir / "roads.geojson"

    with open(site_path) as f:
        site_data = json.load(f)

    with open(roads_path) as f:
        roads_data = json.load(f)

    parameters = deepcopy(
        ProjectCreate.model_config["json_schema_extra"]["examples"][0][
            "parameters"]
    )
    data = {
        "name": "Test Project",
        "description": "Test Project Description",
        "parameters": parameters,
        "site": roads_data,
        "roads": site_data
    }
    r = client.put(
        f"{settings.API_V1_STR}/projects/{uuid}",
        json=data,
        headers=superuser_token_headers,
    )
    assert r.status_code == 400
    assert r.json()["detail"] == (
        "Expected geometry type 'Polygon', got 'LineString' in feature 0"
    )

    # ----------------------------------------------------
    # UPDATE TEST WORKS
    # ----------------------------------------------------
    with open(site_path) as f:
        site_data = json.load(f)

    with open(roads_path) as f:
        roads_data = json.load(f)

    parameters["neighbourhood"]["public_roads"]["width_of_arteries_m"] = 10
    parameters["neighbourhood"]["public_roads"]["width_of_secondaries_m"] = 5

    data = {
        "name": "Test Project",
        "description": "Test Project Description",
        "parameters": parameters
    }
    r = client.put(
        f"{settings.API_V1_STR}/projects/{uuid}",
        json=data,
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    project = Project.get(session=db, uuid=uuid, user=superuser)
    assert project.name == "Test Project"
    assert project.description == "Test Project Description"
    assert project.parameters.neighbourhood.public_roads.width_of_arteries_m == 10
    assert project.parameters.neighbourhood.public_roads.width_of_secondaries_m == 5

    assert project.get_path_roads() == project.folder / "input" / "roads.geojson"
    assert project.get_path_site() == project.folder / "input" / "site.geojson"
    with open(project.get_path_site()) as f:
        assert site_data == json.load(f)
    with open(project.get_path_roads()) as f:
        assert roads_data == json.load(f)

    # Check all steps being rerun
    for step in StepType:
        path = project.get_file_path(
            step, ExtensionType.JSON, filename="task.json"
        )
        with open(path) as f:
            assert json.loads(f.read())["run_at"] != task_uuids[step]

    # ----------------------------------------------------
    # UPDATE TEST WORKS WITH GEOJSON
    # ----------------------------------------------------
    # Load fixture files
    fixtures_dir = Path(__file__).parent / "fixtures"
    site_path = fixtures_dir / "site_new.geojson"
    roads_path = fixtures_dir / "roads_new.geojson"
    with open(site_path) as f:
        new_site_data = json.load(f)

    with open(roads_path) as f:
        new_roads_data = json.load(f)

    parameters["neighbourhood"]["public_roads"]["width_of_arteries_m"] = 10
    parameters["neighbourhood"]["public_roads"]["width_of_secondaries_m"] = 5

    data = {
        "name": "Test Project",
        "description": "Test Project Description",
        "parameters": parameters,
        "site": new_site_data,
        "roads": new_roads_data
    }
    r = client.put(
        f"{settings.API_V1_STR}/projects/{uuid}",
        json=data,
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    project = Project.get(session=db, uuid=uuid, user=superuser)
    assert project.name == "Test Project"
    assert project.description == "Test Project Description"
    assert project.parameters.neighbourhood.public_roads.width_of_arteries_m == 10
    assert project.parameters.neighbourhood.public_roads.width_of_secondaries_m == 5

    assert project.get_path_roads() == project.folder / "input" / "roads.geojson"
    assert project.get_path_site() == project.folder / "input" / "site.geojson"
    with open(project.get_path_site()) as f:
        assert new_site_data == json.load(f)
    with open(project.get_path_roads()) as f:
        assert new_roads_data == json.load(f)

    # Check all steps being rerun
    for step in StepType:
        path = project.get_file_path(
            step, ExtensionType.JSON, filename="task.json"
        )
        with open(path) as f:
            assert json.loads(f.read())["run_at"] != task_uuids[step]


@patch("app.tasks.generate_rue.generate_rue", wraps=generate_rue)
def test_update_task(
        mock_generate_rue, client: TestClient,
        superuser_token_headers: dict[str, str],
        db: Session,
        superuser: User
) -> None:
    """Test update_task."""
    assert mock_generate_rue.call_count == 0

    parameters = (
        ProjectCreate.model_config["json_schema_extra"]["examples"][0][
            "parameters"]
    )
    data = {
        "name": "Test Project",
        "description": "Test Project Description",
        "parameters": parameters
    }
    r = client.post(
        f"{settings.API_V1_STR}/projects",
        json=data,
        headers=superuser_token_headers,
    )
    assert r.status_code == 201

    uuid = r.json()["uuid"]

    project = Project.get(session=db, uuid=uuid, user=superuser)
    assert project.name == "Test Project"
    assert project.description == "Test Project Description"
    assert project.parameters.neighbourhood.public_roads.width_of_arteries_m == 20
    assert project.parameters.neighbourhood.public_roads.width_of_secondaries_m == 15

    step_geojson = {}
    for step in StepType:
        geojson_file = project.get_file_path(
            step, ExtensionType.GEOJSON
        )
        with open(geojson_file) as f:
            step_geojson[step.value] = json.load(f)

    # Check how many call the generate_rue
    assert mock_generate_rue.call_count == len(STEPS) + 1

    # ----------------------------------
    # Update the step
    # ----------------------------------
    target_step = StepType.STREETS
    r = client.put(
        f"{settings.API_V1_STR}/projects/{uuid}/{target_step.value}",
        json={},
        headers=superuser_token_headers,
    )
    assert r.status_code == 422

    # Check remove_step_after
    project.remove_step_after(target_step)
    for step in StepType:
        geojson_file = project.get_file_path(
            step, ExtensionType.GEOJSON
        )
        if step in [StepType.SITE, StepType.STREETS]:
            assert Path(geojson_file).exists() is True
        else:
            assert geojson_file is None

    # Load fixture files
    fixtures_dir = Path(__file__).parent / "fixtures"
    update_geojson = fixtures_dir / "parcel.geojson"
    with open(update_geojson) as f:
        new_geojson = json.load(f)
        r = client.put(
            f"{settings.API_V1_STR}/projects/{uuid}/{target_step.value}",
            json={"geojson": new_geojson},
            headers=superuser_token_headers,
        )
        assert r.status_code == 204

        step_index = STEPS.index(target_step.value)
        remaining_step = len(STEPS) - step_index

        # Check how many call the generate_rue
        assert mock_generate_rue.call_count == (
                len(STEPS) + remaining_step + 1
        )

        # New data
        project = Project.get(session=db, uuid=uuid, user=superuser)
        for step in StepType:
            geojson_file = project.get_file_path(
                step, ExtensionType.GEOJSON
            )
            with open(geojson_file) as f:
                geojson = json.load(f)
                if step == target_step:
                    assert step_geojson[step.value] != geojson
                    assert new_geojson == geojson
                else:
                    assert step_geojson[step.value] == geojson
