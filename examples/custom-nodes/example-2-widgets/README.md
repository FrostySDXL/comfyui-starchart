# Example 2: Node with Configuration Widgets

**Status:** Pattern example
**Level:** Beginner -- builds on example-1 (minimal-node-template)

## What This Example Is

A V1 custom node that demonstrates the full range of INPUT_TYPES widget
options: dropdowns, sliders, toggles, text inputs, and number fields. Shows
how to define optional inputs with defaults and how to use the selected
widget values at execution time.

This is the next step after a basic pass-through node. Real nodes almost
always have configuration -- this shows the standard widget patterns.

## Files

- `brightness_node.py` -- V1 node with multiple widget types

## What to Study

- `INPUT_TYPES` structure for required and optional inputs
- Widget specification syntax: `("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0})`
- Dropdown specification: constant tuple `(["option_a", "option_b"],)` -- no
  `"options"` key
- How widget values arrive in the execute method

## Widget Types Reference

```python
INPUT_TYPES = {
    "required": {
        "image": ("IMAGE",),  # bare type, no widget options
    },
    "optional": {
        # Slider (FLOAT)
        "strength": ("FLOAT", {
            "default": 1.0,
            "min": 0.0,
            "max": 10.0,
            "step": 0.1,
            "round": 0.01,  # precision of UI display
        }),
        # Integer slider
        "passes": ("INT", {
            "default": 2,
            "min": 1,
            "max": 10,
            "step": 1,
        }),
        # Dropdown (constant tuple -- options are strings, no "options" key)
        "mode": (["brighten", "darken", "contrast", "invert"],),
        # Text string input
        "label": ("STRING", {
            "default": "unnamed",
            "multiline": True,  # allow multiline text
        }),
        # Toggle (BOOLEAN)
        "normalize": ("BOOLEAN", {"default": True}),
    }
}
```

## Evidence Level

- V1 INPUT_TYPES specification: documented in ComfyUI source and docs.comfy.org
- Widget behavior: upstream source behavior
- This example: hand-authored to illustrate documented patterns
