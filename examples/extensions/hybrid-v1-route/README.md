# Hybrid V1 Route Example

This example shows the smallest repo-local hybrid extension pattern that combines:

- module-level V1 `NODE_CLASS_MAPPINGS` in `__init__.py`
- one simple `STRING`-based node using the V1 contract described in `src/content/docs/custom-nodes/v1-reference.md`
- one `PromptServer.instance.routes` route in `routes.py`

## What each file demonstrates

- `__init__.py` holds the V1 node class, exports `NODE_CLASS_MAPPINGS`, and calls route registration during package import.
- `routes.py` registers one extension-owned HTTP endpoint with `PromptServer.instance.routes`.

The import-time `register_routes()` call is intentional. ComfyUI extension
packages commonly register routes when the package loads, so this example keeps
that pattern visible. The route helper in `routes.py` uses an idempotency guard
to avoid duplicate registration when the module is imported more than once.

## Why this is a hybrid extension

It combines two server-side extension surfaces in one package:

- a V1 custom node for graph-executable behavior
- a custom route for request/response access

That makes it a hybrid package even though it deliberately omits frontend JavaScript.

## What this example deliberately omits

- frontend JS hooks or panels
- packaging and distribution complexity
- runtime validation and persistence helpers
- advanced startup or lifecycle handling

Use this example as the smallest composition reference. For the V1 node contract itself, read `src/content/docs/custom-nodes/v1-reference.md` instead of treating this README as a second V1 reference.
