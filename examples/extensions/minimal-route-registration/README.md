# Minimal Route Registration Example

**Status:** Starter pattern
**Validation tiers:** static, offline unit-tested, pinned-source, opt-in runtime smoke after installation

## What This Example Shows

This directory isolates the smallest server-side route-registration pattern this
repo recommends showing in examples:

1. get `PromptServer.instance`
2. guard against duplicate registration
3. register one extension-owned route on `PromptServer.instance.routes`
4. return a small JSON response that proves the route is live

## Files

- `__init__.py` - invocation-time wiring that exposes `main()` without
  registering routes at import time
- `routes.py` - minimal idempotent route registration helper

## What This Proves

- a bounded extension can register custom HTTP routes without mixing in custom
  nodes or frontend code
- idempotency guards belong in repo examples so repeated imports do not silently
  duplicate route handlers

## What This Intentionally Leaves Out

- custom-node registration
- frontend panels, commands, or hooks
- persistence, authentication, or production deployment concerns

## Invocation-Time Wiring

This example intentionally does not call `register_routes()` at import time.
Import-time route mutation makes unit tests and static analysis surprising; the
safer teaching shape is to expose `main()` and call it when ComfyUI is loading or
when you explicitly run the example.

The on-disk directory is hyphenated for filesystem clarity, but the import goes
through `spec_from_file_location` to bridge the hyphen/underscore gap.

```bash
python -c "import importlib.util, pathlib; spec = importlib.util.spec_from_file_location('minimal_route_registration', pathlib.Path('examples/extensions/minimal-route-registration/__init__.py')); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); m.main()"
```

`NODE_CLASS_MAPPINGS = {}` is exported only so the directory can be treated as a
loadable custom-node package shape without claiming any graph-executable nodes.

After installing this example in a live ComfyUI runtime, validate the route with:

```bash
python scripts/verify/example_runtime_smoke.py --url http://127.0.0.1:8188 --comfyui-root D:/projects/comfyui-test-runtime --skip-prompt --expect-extension-route
```

Use this as the smallest route surface reference. For broader composition
patterns, compare it with
[`examples/extensions/hybrid-v1-route/`](../hybrid-v1-route/README.md) and the
the published hooks and custom-node pages for route registration and server extension boundaries.
