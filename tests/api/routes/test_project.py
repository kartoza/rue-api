import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import settings
from app.models import ProjectCreate, Project


def test_create_project_empty(client: TestClient) -> None:
    """Test creating a project with empty parameters using API endpoint."""
    login_data = {}
    r = client.post(f"{settings.API_V1_STR}/projects", json=login_data)
    assert r.status_code == 422


def test_create_project_works(client: TestClient) -> None:
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
    r = client.post(f"{settings.API_V1_STR}/projects", json=data)
    assert r.status_code == 201

    uuid = r.json()["uuid"]
    project = Project(uuid=uuid)
    assert project.name == "Test Project"
    assert project.description == "Test Project Description"
    assert project.parameters.neighbourhood.public_roads.width_of_arteries_m == 20
    assert project.parameters.neighbourhood.public_roads.width_of_secondaries_m == 15


def test_create_project_error_input(client: TestClient) -> None:
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
    r = client.post(f"{settings.API_V1_STR}/projects", json=data)
    assert r.status_code == 400
    assert r.json()[
               "detail"] == "Expected geometry type 'Polygon', got 'LineString' in feature 0"


def test_create_project_working_input(client: TestClient) -> None:
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
    r = client.post(f"{settings.API_V1_STR}/projects", json=data)
    assert r.status_code == 201

    uuid = r.json()["uuid"]
    project = Project(uuid=uuid)
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
