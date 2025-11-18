"""Unit tests for Project and Task models and business logic."""

import unittest
import uuid as uuid_pkg
from uuid import UUID

from sqlmodel import Session, SQLModel, create_engine

from app.models.project import (
    Amenities,
    BlockStructureConfig,
    ComponentType,
    CornerBonus,
    FireProtection,
    InitialBuildingPercent,
    LotConfig,
    Neighbourhood,
    OffGridClusterType1,
    OffGridClusterType2,
    OffGridPartitions,
    OnGridPartitions,
    OpenSpaces,
    Project,
    ProjectCreate,
    ProjectParameters,
    PublicRoads,
    PublicSpaces,
    StarterBuildings,
    StarterBuildingsOnArteries,
    StarterBuildingsOnLocals,
    StarterBuildingsOnSecondaries,
    StreetSection,
    Tissue,
    Trees,
    UrbanBlockStructure,
)


class TestProjectModel(unittest.TestCase):
    """Test Project model CRUD operations."""

    def setUp(self):
        """Set up each test with a fresh in-memory database."""
        self.engine = create_engine("sqlite:///:memory:")
        SQLModel.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    def tearDown(self):
        """Clean up after each test."""
        self.session.close()

    def test_create_project_minimal(self):
        """Test creating a project with minimal required fields."""
        # Given
        uuid = uuid_pkg.uuid4()
        project = Project(uuid=uuid)
        project.name = "Test Project"
        project.description = "A test project"
        project.save_to_file()

        # Then
        project = Project(uuid=uuid)
        self.assertIsNotNone(project.uuid)
        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.description, "A test project")
        self.assertIsInstance(project.uuid, UUID)

    def test_create_project_with_parameters(self):
        """Test creating a project with full parameters."""
        # Given
        parameters = {
            "neighbourhood": {
                "public_roads": {
                    "width_of_arteries_m": 20,
                    "width_of_secondaries_m": 15,
                    "width_of_locals_m": 10,
                }
            }
        }
        uuid = uuid_pkg.uuid4()
        project = Project(uuid=uuid)
        project.name = "Full Test Project"
        project.description = "Project with parameters"
        project.project_metadata = {"author": "test"}
        project.parameters = parameters
        project.save_to_file()

        project = Project(uuid=uuid)
        # Then
        self.assertEqual(
            project.parameters["neighbourhood"]["public_roads"][
                "width_of_arteries_m"], 20
        )
        self.assertEqual(project.project_metadata["author"], "test")

    def test_create_project_without_description(self):
        """Test creating a project without optional description."""
        # Given
        uuid = uuid_pkg.uuid4()
        project = Project(uuid=uuid)
        project.name = "Minimal Project"
        project.save_to_file()

        # Then
        project = Project(uuid=uuid)
        self.assertEqual(project.description, "")
        self.assertEqual(project.name, "Minimal Project")


class TestTaskModel(unittest.TestCase):
    """Test Task model CRUD operations."""

    def setUp(self):
        """Set up each test with a fresh in-memory database."""
        self.engine = create_engine("sqlite:///:memory:")
        SQLModel.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    def tearDown(self):
        """Clean up after each test."""
        self.session.close()

    def test_create_task_for_project(self):
        """Test creating a task associated with a project."""
        # Given
        uuid = uuid_pkg.uuid4()
        project = Project(uuid=uuid)
        project.name = "Test Project"
        project.description = "A test project"
        project.save_to_file()

        project.generate()


class TestProjectParametersSchema(unittest.TestCase):
    """Test ProjectParameters schema validation."""

    def test_create_project_parameters_complete(self):
        """Test creating complete ProjectParameters with all nested models."""
        # Given
        public_roads = PublicRoads(
            width_of_arteries_m=20,
            width_of_secondaries_m=15,
            width_of_locals_m=10,
        )
        on_grid_partitions = OnGridPartitions(
            depth_along_arteries_m=40,
            depth_along_secondaries_m=30,
            depth_along_locals_m=20,
        )
        off_grid_partitions = OffGridPartitions(
            cluster_depth_m=45,
            cluster_size_lots=15,
            cluster_width_m=30,
            lot_depth_along_path_m=12.5,
            lot_depth_around_yard_m=10,
        )

        block_structure = BlockStructureConfig(
            off_grid_clusters_in_depth_m=0,
            off_grid_clusters_in_width_m=3,
        )
        urban_block = UrbanBlockStructure(
            along_arteries=block_structure,
            along_secondaries=block_structure,
            along_locals=block_structure,
        )

        trees = Trees(
            show_trees_frontend=True,
            tree_spacing_m=12,
            initial_tree_height_m=8,
            final_tree_height_m=20,
        )
        public_spaces = PublicSpaces(
            open_spaces=OpenSpaces(open_space_percentage=0),
            amenities=Amenities(amenities_percentage=10),
            street_section=StreetSection(sidewalk_width_m=3),
            trees=trees,
        )

        neighbourhood = Neighbourhood(
            public_roads=public_roads,
            on_grid_partitions=on_grid_partitions,
            off_grid_partitions=off_grid_partitions,
            urban_block_structure=urban_block,
            public_spaces=public_spaces,
        )

        lot_config = LotConfig(
            depth_m=40,
            width_m=40,
            front_setback_m=6,
            side_margins_m=6,
            rear_setback_m=6,
            number_of_floors=5,
        )

        cluster_type1 = OffGridClusterType1(
            access_path_width_on_grid_m=3,
            internal_path_width_m=5,
            open_space_width_m=10,
            open_space_length_m=15,
            lot_width_m=6,
            front_setback_m=0,
            side_margins_m=0,
            rear_setback_m=3,
            number_of_floors=2,
        )

        cluster_type2 = OffGridClusterType2(
            internal_path_width_m=3,
            cul_de_sac_width_m=5,
            lot_width_m=4.5,
            lot_depth_behind_cul_de_sac_m=15,
        )

        corner_bonus = CornerBonus(
            description="Density bonus",
            with_artery_percent=40,
            with_secondary_percent=30,
            with_local_percent=20,
        )

        fire_protection = FireProtection(
            fire_proof_partitions_with_6m_margins=False)

        tissue = Tissue(
            on_grid_lots_on_arteries=lot_config,
            on_grid_lots_on_secondaries=lot_config,
            on_grid_lots_on_locals=lot_config,
            off_grid_cluster_type_1=cluster_type1,
            off_grid_cluster_type_2=cluster_type2,
            corner_bonus=corner_bonus,
            fire_protection=fire_protection,
        )

        initial_percent = InitialBuildingPercent(
            initial_width_percent=100,
            initial_depth_percent=60,
            initial_floors_percent=80,
        )

        starter_arteries = StarterBuildingsOnArteries(
            corner_with_other_artery=initial_percent,
            corner_with_secondary=initial_percent,
            corner_with_tertiary=initial_percent,
            regular_lot=initial_percent,
        )

        starter_secondaries = StarterBuildingsOnSecondaries(
            corner_with_other_secondary=initial_percent,
            corner_with_tertiary=initial_percent,
            regular_lot=initial_percent,
        )

        starter_locals = StarterBuildingsOnLocals(
            corner_with_other_local=initial_percent,
            regular_lot=initial_percent,
        )

        starter_buildings = StarterBuildings(
            on_grid_lots_on_arteries=starter_arteries,
            on_grid_lots_on_secondaries=starter_secondaries,
            on_grid_lots_on_locals=starter_locals,
            off_grid_cluster_type_1=initial_percent,
            off_grid_cluster_type_2=initial_percent,
        )

        # When
        parameters = ProjectParameters(
            neighbourhood=neighbourhood,
            tissue=tissue,
            starter_buildings=starter_buildings,
        )

        # Then
        self.assertEqual(
            parameters.neighbourhood.public_roads.width_of_arteries_m, 20)
        self.assertEqual(
            parameters.tissue.corner_bonus.description,
            "Density bonus"
        )
        self.assertEqual(
            parameters.starter_buildings.off_grid_cluster_type_1.initial_width_percent,
            100
        )

    def test_project_parameters_model_dump(self):
        """Test that ProjectParameters can be serialized to dict."""
        # Given
        public_roads = PublicRoads(
            width_of_arteries_m=20,
            width_of_secondaries_m=15,
            width_of_locals_m=10,
        )
        # ... (simplified for brevity)

        # When
        data = public_roads.model_dump()

        # Then
        self.assertIsInstance(data, dict)
        self.assertEqual(data["width_of_arteries_m"], 20)
        self.assertEqual(data["width_of_secondaries_m"], 15)


class TestProjectCreateSchema(unittest.TestCase):
    """Test ProjectCreate schema."""

    def test_project_create_has_examples(self):
        """Test that ProjectCreate schema has example data."""
        # Given / When
        config = ProjectCreate.model_config

        # Then
        self.assertIn("json_schema_extra", config)
        self.assertIn("examples", config["json_schema_extra"])
        examples = config["json_schema_extra"]["examples"]
        self.assertGreater(len(examples), 0)

        example = examples[0]
        self.assertIn("name", example)
        self.assertIn("parameters", example)
        self.assertIn("neighbourhood", example["parameters"])
        self.assertIn("tissue", example["parameters"])
        self.assertIn("starter_buildings", example["parameters"])


class TestSwaggerUIDocumentation(unittest.TestCase):
    """Test Swagger UI and OpenAPI documentation."""

    def test_project_parameters_schema_structure(self):
        """Test that ProjectParameters has proper nested structure."""
        # Given
        from pydantic import TypeAdapter

        adapter = TypeAdapter(ProjectParameters)
        schema = adapter.json_schema()

        # Then
        self.assertEqual(schema["type"], "object")
        self.assertIn("properties", schema)
        self.assertIn("neighbourhood", schema["properties"])
        self.assertIn("tissue", schema["properties"])
        self.assertIn("starter_buildings", schema["properties"])

        # Check required fields
        self.assertIn("required", schema)
        self.assertIn("neighbourhood", schema["required"])
        self.assertIn("tissue", schema["required"])
        self.assertIn("starter_buildings", schema["required"])

    def test_component_type_enum_values(self):
        """Test that ComponentType enum has all expected values."""
        # Given / When
        component_values = [ct.value for ct in ComponentType]

        # Then
        expected = ["site", "streets", "clusters", "public", "subdivision",
                    "footprint", "building_start", "building_max"]
        self.assertEqual(component_values, expected)


if __name__ == "__main__":
    unittest.main()
