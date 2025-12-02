from typing import Any

from fastapi import HTTPException

from app.api.deps import SessionDep
from app.models.project import Project, ProjectCreate, ProjectDetailResponse


def validate_geojson_feature_collection(
        data: dict[str, Any],
        geometry_type: str = None
) -> None:
    """Validate GeoJSON FeatureCollection structure."""
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=400,
            detail=f"Expected GeoJSON FeatureCollection, got {type(data)}"
        )

    if data.get("type") != "FeatureCollection":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Expected type 'FeatureCollection', "
                f"got '{data.get('type')}'"
            )
        )

    features = data.get("features", [])
    if not isinstance(features, list):
        raise HTTPException(status_code=400, detail="Features must be a list")

    if not features:
        raise HTTPException(
            status_code=400,
            detail=f"At least one {geometry_type} feature is required"
        )

    for idx, feature in enumerate(features):
        if not isinstance(feature, dict):
            raise HTTPException(
                status_code=400, detail=f"Feature {idx} must be an object"
            )

        geometry = feature.get("geometry")
        if not geometry:
            raise HTTPException(
                status_code=400, detail=f"Feature {idx} missing geometry"
            )

        geom_type = geometry.get("type")
        if geometry_type and geom_type != geometry_type:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Expected geometry type '{geometry_type}', "
                    f"got '{geom_type}' in feature {idx}"
                ),
            )


def update_project(
        project: Project, project_in: ProjectCreate, session: SessionDep
) -> ProjectDetailResponse:
    """Update project with GeoJSON validation."""
    if project_in.site is not None:
        validate_geojson_feature_collection(project_in.site, "Polygon")
        project.save_site(project_in.site)

    if project_in.roads is not None:
        validate_geojson_feature_collection(project_in.roads, "LineString")
        project.save_roads(project_in.roads)

    project.project_metadata = project_in.project_metadata or {}
    project.insert_parameters(project_in.parameters)
    project.update(session=session)

    # Run task
    project.generate()
    return ProjectDetailResponse(
        uuid=project.uuid,
        name=project_in.name,
        description=project.description,
        parameters=project.parameters,
        project_metadata=project.project_metadata,
    )
