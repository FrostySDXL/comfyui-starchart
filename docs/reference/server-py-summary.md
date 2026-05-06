# Server.py Summary

**Last Synced:** 2026-04-30
**Source:** references/snapshots/2026-04-30/comfyui-core-v0.20.1/server.py
**Evidence:** Source-backed from pinned snapshots

## Overview

Generated from `references/raw/server_endpoints.json`.

## Route Summary

| Method | Route | Description | Parameters |
| --- | --- | --- | --- |
| GET | /ws |  | clientId (query) default= |
| GET | / |  | - |
| GET | /embeddings |  | - |
| GET | /models |  | - |
| GET | /models/{folder} |  | folder (path) |
| GET | /extensions |  | - |
| POST | /upload/image |  | image (form); overwrite (form); type (form); subfolder (form) default= |
| POST | /upload/mask |  | image (form); overwrite (form); type (form); subfolder (form) default= |
| GET | /view |  | filename (query); subfolder (query); preview (query); channel (query) default=; type (query) default=output |
| GET | /view_metadata/{folder_name} |  | folder_name (path); filename (query) |
| GET | /system_stats |  | - |
| GET | /features |  | - |
| GET | /prompt |  | - |
| GET | /object_info |  | - |
| GET | /object_info/{node_class} |  | node_class (path) |
| GET | /api/jobs | List all jobs with filtering, sorting, and pagination. Query parameters: status: Filter by status (comma-separated): pending, in_progress, completed, failed workflow_id: Filter by workflow ID sort_by: Sort field: created_at (default), execution_duration sort_order: Sort direction: asc, desc (default) limit: Max items to return (positive integer) offset: Items to skip (non-negative integer, default 0) | status (query); workflow_id (query); sort_by (query) default=created_at; sort_order (query) default=desc; limit (query); offset (query) |
| GET | /api/jobs/{job_id} | Get a single job by ID. | job_id (path) |
| GET | /history |  | max_items (query); offset (query) |
| GET | /history/{prompt_id} |  | prompt_id (path) |
| GET | /queue |  | - |
| POST | /prompt |  | number (json); front (json); prompt (json); partial_execution_targets (json); extra_data (json); client_id (json); prompt_id (json) |
| POST | /queue |  | clear (json); delete (json) |
| POST | /interrupt |  | prompt_id (json) |
| POST | /free |  | unload_models (json) default=False; free_memory (json) default=False |
| POST | /history |  | clear (json); delete (json) |

## Response Summary

| Route | Kind | Status Codes | Summary |
| --- | --- | --- | --- |
| /ws | websocket | 101 | WebSocket connection upgrade. |
| / | file | 200 | File response with inferred content type. |
| /embeddings | json | 200 | JSON response. |
| /models | json | 200 | JSON response. |
| /models/{folder} | json | 200, 404 | JSON response. |
| /extensions | json | 200 | JSON response. |
| /upload/image | json | 200, 400 | JSON object with fields: name, subfolder, type, asset. |
| /upload/mask | json | 200, 400 | JSON object with fields: name, subfolder, type, asset. |
| /view | file | 200 | File response with inferred content type. |
| /view_metadata/{folder_name} | json | 200, 404 | JSON response. |
| /system_stats | json | 200 | JSON object with fields: system, os, ram_total, ram_free, comfyui_version, required_frontend_version, installed_templates_version, required_templates_version, python_version, pytorch_version, embedded_python, argv, devices, name, type, index, vram_total, vram_free, torch_vram_total, torch_vram_free. |
| /features | json | 200 | JSON response. |
| /prompt | json | 200 | JSON response. |
| /object_info | json | 200 | JSON response. |
| /object_info/{node_class} | json | 200 | JSON response. |
| /api/jobs | json | 200, 400 | JSON object with fields: jobs, pagination, offset, limit, total, has_more. |
| /api/jobs/{job_id} | json | 200, 400, 404 | JSON response. |
| /history | json | 200 | JSON response. |
| /history/{prompt_id} | json | 200 | JSON response. |
| /queue | json | 200 | JSON object with fields: queue_running, queue_pending. |
| /prompt | json | 200, 400 | JSON object with fields: prompt_id, number, node_errors. |
| /queue | empty | 200 | Empty acknowledgement response. |
| /interrupt | empty | 200 | Empty acknowledgement response. |
| /free | empty | 200 | Empty acknowledgement response. |
| /history | empty | 200 | Empty acknowledgement response. |

## Structured Return Details

| Route | Fields | Notes |
| --- | --- | --- |
| /models/{folder} | - | Returns 404 when the requested resource is not found. |
| /upload/image | name, subfolder, type, asset | Returns 400 for validation failures or bad requests. |
| /upload/mask | name, subfolder, type, asset | Returns 400 for validation failures or bad requests. |
| /view_metadata/{folder_name} | - | Returns 404 when the requested resource is not found. |
| /system_stats | system, os, ram_total, ram_free, comfyui_version, required_frontend_version, installed_templates_version, required_templates_version, python_version, pytorch_version, embedded_python, argv, devices, name, type, index, vram_total, vram_free, torch_vram_total, torch_vram_free | - |
| /api/jobs | jobs, pagination, offset, limit, total, has_more | Returns 400 for validation failures or bad requests. |
| /api/jobs/{job_id} | - | Returns 404 when the requested resource is not found. Returns 400 for validation failures or bad requests. |
| /queue | queue_running, queue_pending | - |
| /prompt | prompt_id, number, node_errors | Returns 400 for validation failures or bad requests. |

## Update Process

Regenerate this page after refreshing endpoint JSON.
