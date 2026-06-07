"""Minimal caveated V3 ComfyNode shape.

This example is illustrative only. See README.md for the evidence caveats around
Python-side V3 discovery and entrypoint behavior.
"""

from __future__ import annotations

from comfy_api.latest import io


class ExampleSevenV3Node(io.ComfyNode):
    """Echo one string through a V3 schema-first node shape."""

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="ExampleSevenV3Node",
            display_name="Example 7 V3 Caveated Node",
            category="examples/starchart",
            inputs=[io.String.Input("text")],
            outputs=[io.String.Output()],
        )

    @classmethod
    def execute(cls, text: str):
        return io.NodeOutput(text)
