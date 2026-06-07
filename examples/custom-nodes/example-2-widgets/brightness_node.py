"""V1 node demonstrating INPUT_TYPES widget configuration options.

Shows dropdown, slider, text input, toggle, and integer widget patterns.
"""

import torch
from server import PromptServer


class BrightnessNode:
    CATEGORY = "example/widgets"
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "adjust_brightness"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                # FLOAT slider
                "strength": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.1,
                    "round": 0.01,
                }),
                # Dropdown constant
                "mode": (["brighten", "darken", "contrast", "invert"],),
                # Text input
                "label": ("STRING", {
                    "default": "brightness_pass",
                    "multiline": False,
                }),
                # Integer slider
                "passes": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 5,
                    "step": 1,
                }),
                # Boolean toggle
                "normalize": ("BOOLEAN", {"default": True}),
            }
        }

    def adjust_brightness(self, image, strength=1.0, mode="brighten",
                          label="brightness_pass", passes=1, normalize=True):
        result = image

        for _ in range(passes):
            if mode == "brighten":
                # Multiply by strength factor
                result = result * strength
            elif mode == "darken":
                result = result / max(strength, 1e-8)
            elif mode == "contrast":
                # Center around 0.5, scale by strength
                result = (result - 0.5) * strength + 0.5
            elif mode == "invert":
                result = 1.0 - result

        if normalize:
            # Clip to valid range
            result = torch.clamp(result, 0.0, 1.0)

        # Send a message to the frontend
        PromptServer.instance.send_sync(
            "example.brightness.message",
            {
                "label": label,
                "mode": mode,
                "passes": passes,
            },
        )

        return (result,)


NODE_CLASS_MAPPINGS = {
    "Brightness Node": BrightnessNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Brightness Node": "Brightness / Contrast",
}
