"""V1 node: metadata/utility node for the example-5 package.

Demonstrates a companion utility node that can be used alongside
TextProcessorNode. This node wraps another node's output or provides
summary information about a text pipeline.
"""

from datetime import datetime


class TextMetadataNode:
    CATEGORY = "example/text"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("timestamp", "pipeline_summary")
    FUNCTION = "get_metadata"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_input": ("STRING", {"multiline": False}),
            },
            "optional": {
                "label": ("STRING", {"default": "pipeline"}),
            }
        }

    def get_metadata(self, text_input, label="pipeline"):
        timestamp = datetime.now().isoformat()
        word_count = len(text_input.split())
        char_count = len(text_input)
        summary = f"{label}: {word_count} words, {char_count} chars"
        return (timestamp, summary)


NODE_CLASS_MAPPINGS = {
    "Text Metadata": TextMetadataNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Text Metadata": "Text Metadata",
}
