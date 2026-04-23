"""nodes/__init__.py -- aggregates all node modules for the example-5 package."""

from .text_processor_node import (
    NODE_CLASS_MAPPINGS as TEXT_PROCESSOR_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as TEXT_PROCESSOR_DISPLAY,
)
from .text_metadata_node import (
    NODE_CLASS_MAPPINGS as TEXT_METADATA_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as TEXT_METADATA_DISPLAY,
)

# Re-export so __init__.py can aggregate them
__all__ = [
    "TEXT_PROCESSOR_MAPPINGS",
    "TEXT_PROCESSOR_DISPLAY",
    "TEXT_METADATA_MAPPINGS",
    "TEXT_METADATA_DISPLAY",
]
