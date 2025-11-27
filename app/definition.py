from enum import Enum


class TaskStatus(str, Enum):
    """Task status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class StepType(str, Enum):
    """Component type enumeration."""

    SITE = "site"
    STREETS = "streets"
    CLUSTERS = "clusters"
    PUBLIC = "public"
    SUBDIVISION = "subdivision"
    FOOTPRINT = "footprint"
    BUILDING_START = "building_start"
    BUILDING_MAX = "building_max"


class ExtensionType(str, Enum):
    """Extension type enumeration."""

    GEOJSON = "geojson"
    GLTF = "gltf"
    JSON = "json"


STEPS = [
    StepType.SITE.value,
    StepType.STREETS.value,
    StepType.CLUSTERS.value,
    StepType.PUBLIC.value,
    StepType.SUBDIVISION.value,
    StepType.FOOTPRINT.value,
    StepType.BUILDING_START.value,
    StepType.BUILDING_MAX.value
]
