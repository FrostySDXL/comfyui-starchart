"""In-memory timing collector for the benchmark harness example."""

from __future__ import annotations

import threading
import time
from typing import Any


class BenchmarkMetricsCollector:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active: dict[tuple[str, str], float] = {}
        self._metrics: dict[tuple[str, str], dict[str, Any]] = {}
        self._latest_prompt_id: str | None = None
        self._hook_status = {
            "installed": False,
            "detail": "progress handler not installed yet",
        }

    def set_hook_status(self, *, installed: bool, detail: str) -> None:
        with self._lock:
            self._hook_status = {
                "installed": installed,
                "detail": detail,
            }

    def _key(self, prompt_id: Any, node_id: Any) -> tuple[str, str] | None:
        if node_id is None:
            return None
        return (str(prompt_id or "unknown"), str(node_id))

    def _ensure_metric(
        self,
        key: tuple[str, str],
        *,
        prompt_id: Any,
        node_id: Any,
        class_type: Any = None,
        display_node: Any = None,
    ) -> dict[str, Any]:
        metric = self._metrics.setdefault(
            key,
            {
                "prompt_id": str(prompt_id or "unknown"),
                "node_id": str(node_id),
                "class_type": class_type,
                "display_node": display_node,
                "runs": 0,
                "total_duration_ms": 0.0,
                "last_duration_ms": None,
                "finish_without_start": 0,
                "active": False,
            },
        )
        if class_type is not None:
            metric["class_type"] = class_type
        if display_node is not None:
            metric["display_node"] = display_node
        return metric

    def record_start(
        self,
        *,
        prompt_id: Any,
        node_id: Any,
        class_type: Any = None,
        display_node: Any = None,
    ) -> None:
        key = self._key(prompt_id, node_id)
        if key is None:
            return

        with self._lock:
            if prompt_id is not None:
                self._latest_prompt_id = str(prompt_id)
            metric = self._ensure_metric(
                key,
                prompt_id=prompt_id,
                node_id=node_id,
                class_type=class_type,
                display_node=display_node,
            )
            metric["active"] = True
            self._active[key] = time.perf_counter()

    def record_finish(
        self,
        *,
        prompt_id: Any,
        node_id: Any,
        class_type: Any = None,
        display_node: Any = None,
    ) -> None:
        key = self._key(prompt_id, node_id)
        if key is None:
            return

        with self._lock:
            metric = self._ensure_metric(
                key,
                prompt_id=prompt_id,
                node_id=node_id,
                class_type=class_type,
                display_node=display_node,
            )
            started_at = self._active.pop(key, None)
            metric["active"] = False
            if started_at is None:
                metric["finish_without_start"] += 1
                return

            duration_ms = round((time.perf_counter() - started_at) * 1000.0, 3)
            metric["runs"] += 1
            metric["last_duration_ms"] = duration_ms
            metric["total_duration_ms"] = round(metric["total_duration_ms"] + duration_ms, 3)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            node_metrics = []
            for metric in self._metrics.values():
                average_duration_ms = None
                if metric["runs"]:
                    average_duration_ms = round(metric["total_duration_ms"] / metric["runs"], 3)

                node_metrics.append(
                    {
                        **metric,
                        "average_duration_ms": average_duration_ms,
                    }
                )

            node_metrics.sort(key=lambda item: (item["prompt_id"], item["node_id"]))

            return {
                "hook_status": dict(self._hook_status),
                "latest_prompt_id": self._latest_prompt_id,
                "active_node_count": len(self._active),
                "node_metrics": node_metrics,
            }


class BenchmarkProgressHandler:
    """Minimal handler object matching ComfyUI's pinned ProgressHandler contract."""

    def __init__(self, collector: BenchmarkMetricsCollector) -> None:
        self.name = "benchmark-harness"
        self.enabled = True
        self.collector = collector
        self.registry: Any = None

    def set_registry(self, registry: Any) -> None:
        self.registry = registry

    def _node_context(self, node_id: str) -> dict[str, Any]:
        class_type = None
        display_node = None
        registry = self.registry
        dynprompt = getattr(registry, "dynprompt", None)
        if dynprompt is not None:
            try:
                node = dynprompt.get_node(node_id)
            except Exception:
                node = None
            if isinstance(node, dict):
                class_type = node.get("class_type")
            try:
                display_node = dynprompt.get_display_node_id(node_id)
            except Exception:
                display_node = None

        return {
            "node_id": node_id,
            "class_type": class_type,
            "display_node": display_node,
        }

    def start_handler(self, node_id: str, state: Any, prompt_id: str) -> None:
        del state
        self.collector.record_start(prompt_id=prompt_id, **self._node_context(node_id))

    def update_handler(
        self,
        node_id: str,
        value: float,
        max_value: float,
        state: Any,
        prompt_id: str,
        image: Any = None,
    ) -> None:
        del node_id, value, max_value, state, prompt_id, image

    def finish_handler(self, node_id: str, state: Any, prompt_id: str) -> None:
        del state
        self.collector.record_finish(prompt_id=prompt_id, **self._node_context(node_id))

    def reset(self) -> None:
        return None

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False


def install_progress_handler(handler: BenchmarkProgressHandler) -> tuple[bool, str]:
    try:
        import comfy_execution.progress as progress
    except Exception as exc:
        return False, f"unable to import comfy_execution.progress: {exc}"

    if getattr(progress, "_benchmark_harness_handler", None) is handler:
        return True, "progress handler already installed"

    progress._benchmark_harness_handler = handler

    original_reset = getattr(progress, "_benchmark_harness_original_reset", None)
    if original_reset is None:
        original_reset = progress.reset_progress_state
        progress._benchmark_harness_original_reset = original_reset

        def wrapped_reset(*args: Any, **kwargs: Any) -> Any:
            result = original_reset(*args, **kwargs)
            active_handler = getattr(progress, "_benchmark_harness_handler", None)
            if active_handler is not None:
                progress.add_progress_handler(active_handler)
            return result

        progress.reset_progress_state = wrapped_reset

    progress.add_progress_handler(handler)
    return True, "installed and re-registers after reset_progress_state"
