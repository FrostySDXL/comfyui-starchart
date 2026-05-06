class StringEchoReference:
    CATEGORY = "examples/v1"
    FUNCTION = "run"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("original", "uppercased")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "hello", "multiline": False}),
            }
        }

    def run(self, text):
        return (text, text.upper())


NODE_CLASS_MAPPINGS = {
    "StringEchoReference": StringEchoReference,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StringEchoReference": "String Echo Reference",
}
