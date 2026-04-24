"""Minimal benchmark harness extension example.

This package demonstrates a very small hybrid extension:
- Python-side timing collection during execution
- one JSON route for current stats
- one frontend panel served through WEB_DIRECTORY

Evidence boundary:
- route registration is source-backed in the pinned server snapshot
- execution progress registration is source-backed in the pinned execution and
  comfy_execution/progress snapshots
- the handler implements only the pinned ProgressHandler surface it needs for
  start/finish timing collection
"""

from .metrics_collector import BenchmarkMetricsCollector, BenchmarkProgressHandler, install_progress_handler
from .routes import register_routes

WEB_DIRECTORY = "./web"

COLLECTOR = BenchmarkMetricsCollector()
HANDLER = BenchmarkProgressHandler(COLLECTOR)

installed, detail = install_progress_handler(HANDLER)
COLLECTOR.set_hook_status(installed=installed, detail=detail)
register_routes(COLLECTOR)

__all__ = ["WEB_DIRECTORY"]
