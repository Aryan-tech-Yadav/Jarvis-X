from .config import config
from .models import models
from .services import services

def initialize_imports() -> None:
    """Initialize imports."""
    initialize_imports()

def register_classes() -> None:
    """Register classes."""
    models.register_classes()
    services.register_classes()

if __name__ == "__main__":
    initialize_imports()
    register_classes()