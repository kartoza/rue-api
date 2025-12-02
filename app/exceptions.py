
class ProjectDoesNotExists(Exception):
    """Project does not exist."""

    response_schema = {
        "description": "Project not found",
        "content": {
            "application/json": {
                "example": {"detail": "Project does not exist"}
            }
        },
    }

    def __init__(self, message):
        """Initialize the exception."""
        self.message = message
        super().__init__(self.message)