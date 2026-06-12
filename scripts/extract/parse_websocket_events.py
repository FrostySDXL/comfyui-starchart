"""Extract ComfyUI WebSocket event contracts from pinned source snapshots."""

from __future__ import annotations

import argparse
import ast
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.common.path_normalization import normalize_repo_path, normalize_repo_relative_path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "references" / "raw" / "websocket_events.json"

WEBSOCKET_EVENT_COVERAGE = {
    "description": "Source-observed ComfyUI WebSocket and binary event contracts.",
    "guaranteed_fields": [
        "metadata",
        "coverage",
        "events",
        "events.name",
        "events.direction",
        "events.server_sources",
        "events.frontend_listeners",
        "events.traceability",
        "binary_events",
        "binary_events.name",
        "binary_events.traceability",
    ],
    "best_effort_fields": [
        "events.payload_fields",
        "events.payload_notes",
        "events.ast_scan_notes",
        "binary_events.enum_value",
        "binary_events.server_sources",
        "binary_events.frontend_listeners",
        "binary_events.payload_notes",
    ],
    "deferred": [
        "Runtime-computed payload shapes are summarized only when explicit source keys are visible.",
        "Computed event names and unresolvable dynamic dispatch paths are not exhaustive.",
    ],
    "ast_scan_notes": [],
}


class _ParentAnnotator(ast.NodeVisitor):
    def visit(self, node: ast.AST) -> Any:  # noqa: ANN401 - ast visitor API
        for child in ast.iter_child_nodes(node):
            setattr(child, "parent", node)
        return super().visit(node)


def _repo_relative(path: str | Path) -> str:
    return normalize_repo_relative_path(path, REPO_ROOT)


def _parse_python(source: str, source_file: str, coverage: dict[str, Any]) -> ast.Module | None:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        coverage["ast_scan_notes"].append(f"{source_file}: Python AST parse failed: {exc}")
        return None
    _ParentAnnotator().visit(tree)
    return tree


def _source_function(node: ast.AST) -> str | None:
    current = getattr(node, "parent", None)
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current.name
        current = getattr(current, "parent", None)
    return None


def _literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _binary_member(node: ast.AST | None) -> str | None:
    if (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "BinaryEventTypes"
    ):
        return node.attr
    return None


def _explicit_dict_fields(node: ast.AST | None) -> list[str]:
    if not isinstance(node, ast.Dict):
        return []
    fields: list[str] = []
    for key in node.keys:
        value = _literal_string(key) if key is not None else None
        if value is not None:
            fields.append(value)
    return fields


def _assignment_dict_fields(call_node: ast.Call, variable_name: str) -> list[str]:
    current = getattr(call_node, "parent", None)
    while current is not None and not isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
        current = getattr(current, "parent", None)
    if current is None:
        return []
    fields: list[str] = []
    for stmt in getattr(current, "body", []):
        if getattr(stmt, "lineno", 0) >= getattr(call_node, "lineno", 0):
            break
        if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
            continue
        target = stmt.targets[0]
        if isinstance(target, ast.Name) and target.id == variable_name:
            fields = _explicit_dict_fields(stmt.value)
    return fields


def _payload_fields(call_node: ast.Call, payload_arg: ast.AST | None) -> list[str]:
    literal_fields = _explicit_dict_fields(payload_arg)
    if literal_fields:
        return literal_fields
    if isinstance(payload_arg, ast.Name):
        return _assignment_dict_fields(call_node, payload_arg.id)
    return []


def _trace(source_file: str, node: ast.AST, method: str) -> dict[str, Any]:
    return {
        "source_file": source_file,
        "source_function": _source_function(node),
        "line": getattr(node, "lineno", None),
        "method": method,
    }


def _resolve_add_message_calls(tree: ast.Module) -> dict[str, list[ast.Call]]:
    calls: dict[str, list[ast.Call]] = defaultdict(list)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "add_message" or not node.args:
            continue
        event_name = _literal_string(node.args[0])
        if event_name:
            calls[event_name].append(node)
    return calls


def _extract_protocol_binary_events(
    sources: dict[str, str], coverage: dict[str, Any]
) -> tuple[dict[str, int], str | None]:
    protocol_item = next(
        ((path, text) for path, text in sources.items() if path.endswith("protocol.py")), None
    )
    if protocol_item is None:
        coverage["deferred"].append("protocol.py missing; binary_events extraction deferred.")
        return {}, None
    source_file, source = protocol_item
    tree = _parse_python(source, source_file, coverage)
    if tree is None:
        coverage["deferred"].append(
            "protocol.py could not be parsed; binary_events extraction deferred."
        )
        return {}, source_file
    values: dict[str, int] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != "BinaryEventTypes":
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
                continue
            target = stmt.targets[0]
            if (
                isinstance(target, ast.Name)
                and isinstance(stmt.value, ast.Constant)
                and isinstance(stmt.value.value, int)
            ):
                values[target.id] = stmt.value.value
    if not values:
        coverage["deferred"].append("protocol.py did not expose literal BinaryEventTypes values.")
    return values, source_file


def _add_server_source(
    events: dict[str, dict[str, Any]],
    event_name: str,
    source_file: str,
    node: ast.AST,
    method: str,
    payload_fields: list[str] | None = None,
    note: str | None = None,
) -> None:
    event = events[event_name]
    event["server_sources"].append(_trace(source_file, node, method))
    if payload_fields:
        event["payload_fields"].update(payload_fields)
    if note:
        event["payload_notes"].add(note)


def _scan_python_events(
    sources: dict[str, str], coverage: dict[str, Any]
) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    events: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "server_sources": [],
            "payload_fields": set(),
            "payload_notes": set(),
            "dynamic_notes": set(),
        }
    )
    binary_sources: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for source_file, source in sources.items():
        if not source_file.endswith(".py") or source_file.endswith("protocol.py"):
            continue
        tree = _parse_python(source, source_file, coverage)
        if tree is None:
            continue
        add_message_calls = _resolve_add_message_calls(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            method = node.func.attr
            if method not in {"send", "send_sync", "send_json", "send_bytes", "add_message"}:
                continue
            first_arg = node.args[0] if node.args else None
            event_name = _literal_string(first_arg)
            binary_name = _binary_member(first_arg)
            if binary_name:
                binary_sources[binary_name].append(_trace(source_file, node, method))
                continue
            if event_name:
                payload_fields = _payload_fields(node, node.args[1] if len(node.args) > 1 else None)
                _add_server_source(events, event_name, source_file, node, method, payload_fields)
                continue
            if method in {"send", "send_sync", "send_json"} and isinstance(first_arg, ast.Name):
                for resolved_name, caller_nodes in add_message_calls.items():
                    for caller in caller_nodes:
                        payload_fields = _payload_fields(
                            caller, caller.args[1] if len(caller.args) > 1 else None
                        )
                        _add_server_source(
                            events,
                            resolved_name,
                            source_file,
                            caller,
                            f"add_message->{method}",
                            payload_fields,
                            "Resolved through add_message dynamic dispatch.",
                        )
                        events[resolved_name]["dynamic_notes"].add(
                            "Resolved add_message(event, data) dynamic dispatch from literal caller arguments; shared add_message dynamic-dispatch resolver."
                        )
    return events, binary_sources


def _strip_ts_comments(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
    return re.sub(r"//.*", "", source)


def _method_body(source: str, method_name: str) -> str | None:
    anchor = source.find(method_name)
    if anchor == -1:
        return None
    brace_start = source.find("{", anchor)
    if brace_start == -1:
        return None
    depth = 0
    for index in range(brace_start, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[brace_start + 1 : index]
    return None


def _scan_frontend_listeners(
    sources: dict[str, str], coverage: dict[str, Any]
) -> dict[str, list[dict[str, Any]]]:
    listeners: dict[str, list[dict[str, Any]]] = defaultdict(list)
    app_item = next(
        ((path, text) for path, text in sources.items() if path.endswith("app.ts")), None
    )
    if app_item is None:
        coverage["deferred"].append("app.ts missing; frontend listener extraction deferred.")
        return listeners
    source_file, source = app_item
    body = _method_body(source, "addApiUpdateHandlers")
    if body is None:
        coverage["deferred"].append(
            "app.ts addApiUpdateHandlers body not found; frontend listeners deferred."
        )
        return listeners
    body = _strip_ts_comments(body)
    for match in re.finditer(r"api\.addEventListener\(\s*['\"]([^'\"]+)['\"]", body):
        event_name = match.group(1)
        line = source[: source.find(match.group(0))].count("\n") + 1
        listeners[event_name].append(
            {
                "source_file": source_file,
                "source_function": "addApiUpdateHandlers",
                "line": line,
                "method": "api.addEventListener",
            }
        )
    return listeners


def _direction(event_name: str, has_server: bool, has_frontend: bool) -> str:
    if event_name == "feature_flags":
        return "bidirectional"
    if has_server:
        return "server_to_client"
    if has_frontend:
        return "client_to_server"
    return "unknown"


def _event_entry(
    name: str, event_data: dict[str, Any], frontend_listeners: list[dict[str, Any]]
) -> dict[str, Any]:
    server_sources = event_data.get("server_sources", [])
    payload_notes = sorted(event_data.get("payload_notes", set()))
    if not server_sources and name == "progress":
        payload_notes.append(
            "supplied sources did not include main.py; progress server evidence degraded."
        )
    if not server_sources and frontend_listeners:
        payload_notes.append("No server source evidence found in supplied source set.")
        payload_notes.append(
            "listener-only event direction inferred as client_to_server from frontend listener evidence."
        )
    return {
        "name": name,
        "direction": _direction(name, bool(server_sources), bool(frontend_listeners)),
        "server_sources": server_sources,
        "frontend_listeners": frontend_listeners,
        "payload_fields": sorted(event_data.get("payload_fields", set())),
        "payload_notes": payload_notes,
        "ast_scan_notes": [],
        "traceability": {
            "strategy": "ast_send_call_and_frontend_listener_merge",
            "notes": sorted(event_data.get("dynamic_notes", set())),
        },
    }


def _binary_entry(
    name: str,
    enum_value: int,
    protocol_file: str | None,
    server_sources: list[dict[str, Any]],
    frontend_listeners: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    listener_names = [f"b_{name.lower()}"]
    if name == "PREVIEW_IMAGE_WITH_METADATA":
        listener_names.append("b_preview_with_metadata")
    if name == "PREVIEW_IMAGE":
        listener_names.append("b_preview")
    listeners = [
        entry
        for listener_name in listener_names
        for entry in frontend_listeners.get(listener_name, [])
    ]
    return {
        "name": name,
        "enum_value": enum_value,
        "server_sources": server_sources,
        "frontend_listeners": listeners,
        "payload_notes": [],
        "traceability": {
            "source_file": protocol_file,
            "source_function": "BinaryEventTypes",
            "strategy": "protocol_enum_literal",
        },
    }


def build_artifact(
    sources: dict[str, str],
    *,
    version: str | None = "unknown",
    commit: str | None = "unknown",
    frontend_commit: str | None = None,
) -> dict[str, Any]:
    normalized_sources = {normalize_repo_path(path): text for path, text in sources.items()}
    coverage = json.loads(json.dumps(WEBSOCKET_EVENT_COVERAGE))
    events, binary_sources = _scan_python_events(normalized_sources, coverage)
    frontend_listeners = _scan_frontend_listeners(normalized_sources, coverage)
    binary_values, protocol_file = _extract_protocol_binary_events(normalized_sources, coverage)
    if not any(path.endswith("comfy_execution/progress.py") for path in normalized_sources):
        coverage["deferred"].append(
            "comfy_execution/progress.py missing; progress_state extraction deferred."
        )

    all_event_names = set(events) | set(frontend_listeners)
    event_entries = [
        _event_entry(name, events.get(name, {}), frontend_listeners.get(name, []))
        for name in sorted(all_event_names)
        if not name.startswith("b_")
    ]
    if not event_entries and not binary_values:
        coverage["deferred"].append(
            "no recognizable websocket events or binary event enums were found in supplied sources."
        )
    unknown_direction_events = [
        event["name"] for event in event_entries if event.get("direction") == "unknown"
    ]
    if unknown_direction_events:
        coverage["deferred"].append(
            "unknown direction for listener-only events without client_ prefix: "
            + ", ".join(sorted(unknown_direction_events))
            + "."
        )
    binary_entries = [
        _binary_entry(
            name,
            enum_value,
            protocol_file,
            binary_sources.get(name, []),
            frontend_listeners,
        )
        for name, enum_value in sorted(binary_values.items(), key=lambda item: item[1])
    ]

    metadata: dict[str, object] = {
        "sources": list(normalized_sources),
        "extracted_date": datetime.now().strftime("%Y-%m-%d"),
        "version": version or "unknown",
        "commit": commit or "unknown",
    }
    if commit is not None and frontend_commit is not None:
        metadata["commits"] = {"core": commit, "frontend": frontend_commit}

    return {
        "metadata": metadata,
        "coverage": coverage,
        "events": event_entries,
        "binary_events": binary_entries,
    }


def _read_sources(paths: list[str]) -> dict[str, str]:
    sources: dict[str, str] = {}
    for value in paths:
        path = Path(value)
        key = _repo_relative(path)
        sources[key] = path.read_text(encoding="utf-8")
    return sources


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_paths", nargs="+", help="Source files to scan")
    parser.add_argument("--version", default="unknown", help="Snapshot version label")
    parser.add_argument("--commit", default="unknown", help="Snapshot commit label")
    parser.add_argument(
        "--frontend-commit",
        default=None,
        help="Optional frontend snapshot commit for combined core/frontend artifacts",
    )
    parser.add_argument("--output", default=str(OUTPUT_PATH), help="Output JSON path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    data = build_artifact(
        _read_sources(args.source_paths),
        version=args.version,
        commit=args.commit,
        frontend_commit=args.frontend_commit,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted {len(data['events'])} WebSocket events to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
