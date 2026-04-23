"""Example 5: Full Manager-ready extension package.

This package demonstrates a complete, distribution-ready structure:
- Multiple V1 backend nodes under nodes/
- Frontend JavaScript extension under web/js/
- Python dependency management via requirements.txt
- Lifecycle scripts (install, enable, disable, uninstall)
- Manager-aware packaging conventions

Files:
  - __init__.py       -- package entry point
  - nodes/            -- backend node definitions
  - web/js/           -- frontend extension
  - requirements.txt  -- Python dependencies
  - install.py        -- post-install lifecycle hook
  - enable.py         -- re-enable lifecycle hook
  - disable.py        -- disable lifecycle hook
  - uninstall.py      -- pre-removal lifecycle hook

Evidence level:
  - Package structure: community pattern based on ComfyUI-Manager conventions
  - Lifecycle scripts: documented in official ComfyUI-Manager docs
  - This example: hand-authored to illustrate established conventions
"""

from .nodes.text_processor_node import (
    NODE_CLASS_MAPPINGS as _text_processor_mappings,
    NODE_DISPLAY_NAME_MAPPINGS as _text_processor_display,
)
from .nodes.text_metadata_node import (
    NODE_CLASS_MAPPINGS as _text_metadata_mappings,
    NODE_DISPLAY_NAME_MAPPINGS as _text_metadata_display,
)

# Aggregate all node mappings from all node files
NODE_CLASS_MAPPINGS = {}
NODE_CLASS_MAPPINGS.update(_text_processor_mappings)
NODE_CLASS_MAPPINGS.update(_text_metadata_mappings)

NODE_DISPLAY_NAME_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS.update(_text_processor_display)
NODE_DISPLAY_NAME_MAPPINGS.update(_text_metadata_display)

# Tell ComfyUI where to find the frontend extension
WEB_DIRECTORY = "./web/js"

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
