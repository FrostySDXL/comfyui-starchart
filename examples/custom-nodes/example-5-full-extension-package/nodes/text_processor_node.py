"""V1 node: basic text processing node for the example-5 package.

Demonstrates a minimal but complete V1 node that takes a string input,
applies a configurable transformation, and outputs the result.
"""

import re


class TextProcessorNode:
    CATEGORY = "example/text"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("processed_text",)
    FUNCTION = "process_text"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True}),
                "operation": (["uppercase", "lowercase", "strip_html", "word_count"],),
            },
            "optional": {
                "prefix": ("STRING", {"default": ""}),
            }
        }

    def process_text(self, text, operation, prefix=""):
        result = text

        if operation == "uppercase":
            result = result.upper()
        elif operation == "lowercase":
            result = result.lower()
        elif operation == "strip_html":
            result = re.sub(r"<[^>]+>", "", result)
        elif operation == "word_count":
            words = len(result.split())
            result = f"{words} words"

        if prefix:
            result = f"{prefix}{result}"

        return (result,)


NODE_CLASS_MAPPINGS = {
    "Text Processor": TextProcessorNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Text Processor": "Text Processor",
}
