"""Minimal hybrid extension example with one V1 node and one route."""

from .routes import register_routes


class HybridStringEcho:
    CATEGORY = "examples/extensions"
    FUNCTION = "run"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "hello", "multiline": False}),
            }
        }

    def run(self, text):
        return (f"echo: {text}",)


NODE_CLASS_MAPPINGS = {
    "HybridStringEcho": HybridStringEcho,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "HybridStringEcho": "Hybrid String Echo",
}

# Keep route registration at import time because that is the normal ComfyUI
# extension pattern for server-owned routes. routes.py guards against duplicate
# registration if this package is imported more than once.
register_routes()
