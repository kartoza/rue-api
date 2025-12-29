import json
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.definition import StepType, STEPS
from app.exceptions import ProjectDoesNotExists
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
        normal_user_token_headers: dict[str, str],
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
    assert project.created_at is not None
    assert project.updated_at is not None

    # ----------------------------------
    # Test security
    # ----------------------------------
    # Test return projects as non login
    r = client.get(
        f"{settings.API_V1_STR}/projects"
    )
    assert r.status_code == 401

    # Test return projects as other user
    r = client.get(
        f"{settings.API_V1_STR}/projects",
        headers=normal_user_token_headers
    )
    assert r.status_code == 200
    assert len(r.json()) == 0

    # Test return projects
    r = client.get(
        f"{settings.API_V1_STR}/projects",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["uuid"] == uuid
    assert r.json()[0]["name"] == "Test Project"
    assert r.json()[0]["created_at"] == project.created_at.isoformat()
    assert r.json()[0]["updated_at"] == project.updated_at.isoformat()

    # Test return project
    r = client.get(
        f"{settings.API_V1_STR}/projects/{uuid}"
    )
    assert r.status_code == 401
    r = client.get(
        f"{settings.API_V1_STR}/projects/{uuid}",
        headers=normal_user_token_headers
    )
    assert r.status_code == 404

    r = client.get(
        f"{settings.API_V1_STR}/projects/{uuid}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    assert r.json()["uuid"] == uuid
    assert r.json()["name"] == "Test Project"
    assert r.json()["created_at"] == project.created_at.isoformat()
    assert r.json()["updated_at"] == project.updated_at.isoformat()

    # ------------------------------------
    # PATCH
    # ------------------------------------
    last_created_at = project.created_at.isoformat()
    last_updated_at = project.updated_at.isoformat()
    data = {
        "name": "Test Project Patched",
        "description": "Test Project Description Patched"
    }
    r = client.patch(
        f"{settings.API_V1_STR}/projects/{uuid}",
        json=data,
        headers=normal_user_token_headers,
    )
    assert r.status_code == 404

    r = client.patch(
        f"{settings.API_V1_STR}/projects/{uuid}",
        json=data,
        headers=superuser_token_headers,
    )
    assert r.status_code == 200

    r = client.get(
        f"{settings.API_V1_STR}/projects/{uuid}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200

    # Check on model
    project = Project.get(session=db, uuid=uuid, user=superuser)
    assert project.name == "Test Project Patched"
    assert project.description == "Test Project Description Patched"
    assert project.parameters.neighbourhood.public_roads.width_of_arteries_m == 20
    assert project.parameters.neighbourhood.public_roads.width_of_secondaries_m == 15
    assert project.created_at is not None
    assert project.updated_at is not None

    # Check on response
    assert r.json()["uuid"] == uuid
    assert r.json()["name"] == "Test Project Patched"
    assert r.json()["description"] == "Test Project Description Patched"
    assert r.json()["created_at"] == project.created_at.isoformat()
    assert r.json()["updated_at"] == project.updated_at.isoformat()
    assert last_created_at == project.created_at.isoformat()
    assert last_updated_at != project.updated_at.isoformat()


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
        normal_user_token_headers: dict[str, str],
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
            step, filename="task.json"
        )
        with open(path) as f:
            task_uuids[step] = json.loads(f.read())["run_at"]

    # Check last update
    assert project.updated_at is not None
    updated_at = project.updated_at

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
        headers=normal_user_token_headers,
    )
    assert r.status_code == 404

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
        headers=normal_user_token_headers,
    )
    assert r.status_code == 404

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

    # Check last update
    assert project.updated_at is not None
    assert project.updated_at != updated_at
    updated_at = project.updated_at

    assert project.get_path_roads() == project.folder / "input" / "roads.geojson"
    assert project.get_path_site() == project.folder / "input" / "site.geojson"
    with open(project.get_path_site()) as f:
        assert site_data == json.load(f)
    with open(project.get_path_roads()) as f:
        assert roads_data == json.load(f)

    # Get site from API
    r = client.get(
        f"{settings.API_V1_STR}/projects/{uuid}/site_input.geojson",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 404
    r = client.get(
        f"{settings.API_V1_STR}/projects/{uuid}/site_input.geojson",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    assert site_data == r.json()

    # Get roads from API
    r = client.get(
        f"{settings.API_V1_STR}/projects/{uuid}/roads_input.geojson",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 404
    r = client.get(
        f"{settings.API_V1_STR}/projects/{uuid}/roads_input.geojson",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    assert roads_data == r.json()

    # Get task data
    r = client.get(
        f"{settings.API_V1_STR}/projects/{uuid}/site/file/task.json",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 404
    r = client.get(
        f"{settings.API_V1_STR}/projects/{uuid}/site/file/task.json",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200

    # Check all steps being rerun
    for step in StepType:
        path = project.get_file_path(
            step, filename="task.json"
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
        headers=normal_user_token_headers,
    )
    assert r.status_code == 404
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

    # Check last update
    assert project.updated_at is not None
    assert project.updated_at != updated_at
    updated_at = project.updated_at

    r = client.get(
        f"{settings.API_V1_STR}/projects/{uuid}/updated_at",
        headers=superuser_token_headers,
    )
    assert r.text == updated_at.isoformat()

    assert project.get_path_roads() == project.folder / "input" / "roads.geojson"
    assert project.get_path_site() == project.folder / "input" / "site.geojson"
    with open(project.get_path_site()) as f:
        assert new_site_data == json.load(f)
    with open(project.get_path_roads()) as f:
        assert new_roads_data == json.load(f)

    # Check all steps being rerun
    for step in StepType:
        path = project.get_file_path(
            step, filename="task.json"
        )
        with open(path) as f:
            assert json.loads(f.read())["run_at"] != task_uuids[step]
    # ----------------------------------------------------
    # DELETE PROJECT
    # ----------------------------------------------------
    folder_path = project.folder
    assert folder_path.exists() is True

    r = client.delete(
        f"{settings.API_V1_STR}/projects/{uuid}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 404

    r = client.delete(
        f"{settings.API_V1_STR}/projects/{uuid}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 204

    # Verify project no longer exists in database
    with pytest.raises(ProjectDoesNotExists):
        Project.get(session=db, uuid=uuid, user=superuser)

    # Verify folder has been deleted
    assert folder_path.exists() is False


@patch("app.tasks.generate_rue.generate_rue", wraps=generate_rue)
def test_update_task(
        mock_generate_rue, client: TestClient,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
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
            step, "outputs.geojson"
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
            step, "outputs.geojson"
        )
        if step in [StepType.SITE, StepType.STREETS]:
            assert Path(geojson_file).exists() is True
        else:
            assert geojson_file is None

    # Load fixture files
    print("---------------------")
    print(uuid)
    fixtures_dir = Path(__file__).parent / "fixtures"
    update_geojson = fixtures_dir / "parcel.geojson"
    with open(update_geojson) as f:
        new_geojson = json.load(f)
        r = client.put(
            f"{settings.API_V1_STR}/projects/{uuid}/{target_step.value}",
            json={"geojson": new_geojson},
            headers=normal_user_token_headers,
        )
        assert r.status_code == 404

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
                step, "outputs.geojson"
            )
            with open(geojson_file) as f:
                geojson = json.load(f)
                if step == target_step:
                    assert step_geojson[step.value] != geojson
                    assert new_geojson == geojson
                else:
                    assert step_geojson[step.value] == geojson
