"""Invocation-time wiring for the minimal route-registration example."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

NODE_CLASS_MAPPINGS = {}


def _load_routes_module() -> ModuleType | None:
    routes_path = Path(__file__).with_name("routes.py")
    spec = importlib.util.spec_from_file_location("minimal_route_registration_routes", routes_path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except ModuleNotFoundError as exc:
        if exc.name in {"aiohttp", "server"}:
            return None
        raise
    return module


def main() -> None:
    routes_module = _load_routes_module()
    if routes_module is None:
        return
    routes_module.register_routes()


if __name__ == "__main__":
    main()
