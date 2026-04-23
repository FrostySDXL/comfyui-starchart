"""Example 4: Progress UI node package.

This package demonstrates custom server-side event emission paired with
a frontend extension that listens for those events and renders visible
progress feedback in the ComfyUI editor.

The custom event name "my-progress" used in this example is NOT an official
ComfyUI event. It is an example name chosen to show the custom event
emission pattern without implying an official ComfyUI behavior.

Files:
  - progress_emitter_node.py -- V1 node that emits custom progress events
  - web/js/progress-panel.js -- frontend extension that listens and displays

Evidence level:
  - V1 node patterns: upstream source behavior (ComfyUI)
  - Custom event emission: documented in ComfyUI server hooks
  - This example: hand-authored to illustrate documented patterns
"""

from .progress_emitter_node import (
    NODE_CLASS_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS,
    WEB_DIRECTORY,
)

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
