"""V1 node demonstrating custom progress event emission.

This node accepts an IMAGE input, applies a configurable number of
processing iterations, and emits custom progress events during processing.
The event name "my-progress" is an example name -- it is NOT an official
ComfyUI event. See docs.comfy.org or references/snapshots/ for the list
of official ComfyUI events.
"""

import torch
import time
from server import PromptServer


class ProgressEmitterNode:
    CATEGORY = "example/progress"
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("output_image", "status_message")
    FUNCTION = "emit_progress"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "iterations": ("INT", {
                    "default": 5,
                    "min": 1,
                    "max": 20,
                    "step": 1,
                }),
            },
            "optional": {
                "delay_ms": ("FLOAT", {
                    "default": 100.0,
                    "min": 0.0,
                    "max": 2000.0,
                    "step": 10.0,
                }),
            },
            "hidden": {
                "node_id": "UNIQUE_ID",
            }
        }

    def emit_progress(self, image, iterations=5, delay_ms=100.0, node_id=None):
        """Apply a simple brightness modulation and emit progress events.

        The custom event name "my-progress" is used here as an example.
        It is not an official ComfyUI event. Official ComfyUI events are
        documented at docs.comfy.org and in references/snapshots/. Do not
        assume "my-progress" or similar custom names are recognized by
        the ComfyUI server without an accompanying frontend extension that
        listens for them.
        """
        result = image
        total = iterations

        for i in range(iterations):
            # Apply a small brightness modulation per iteration
            factor = 0.95 + (0.05 * (i / max(iterations - 1, 1)))
            result = result * factor

            # Emit a custom progress event.
            # Payload fields: node_id (hidden UNIQUE_ID), progress (float 0.0-1.0), stage (str).
            # This is an EXAMPLE payload shape. Official ComfyUI progress events
            # use different field names and ranges -- see the official API docs.
            PromptServer.instance.send_sync(
                "my-progress",
                {
                    "node_id": node_id,
                    "progress": (i + 1) / total,
                    "stage": f"iteration {i + 1} of {total}",
                },
            )

            # Simulate work delay
            time.sleep(delay_ms / 1000.0)

        # Clamp to valid range
        result = torch.clamp(result, 0.0, 1.0)
        status = f"Applied {iterations} passes, delay={delay_ms:.0f}ms"

        return (result, status)


NODE_CLASS_MAPPINGS = {
    "Progress Emitter": ProgressEmitterNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Progress Emitter": "Progress Emitter",
}

WEB_DIRECTORY = "./web/js"
