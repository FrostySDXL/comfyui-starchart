# Server.py Summary

**Last Synced:** 2026-04-29
**Source:** references/snapshots/2026-04-19/comfyui-core-v0.19.3/server.py

## Overview

Generated from `references/raw/server_endpoints.json`.

## Route Summary

| Method | Route | Description |
| --- | --- | --- |
| GET | /ws |  |
| GET | / |  |
| GET | /embeddings |  |
| GET | /models |  |
| GET | /models/{folder} |  |
| GET | /extensions |  |
| POST | /upload/image |  |
| POST | /upload/mask |  |
| GET | /view |  |
| GET | /view_metadata/{folder_name} |  |
| GET | /system_stats |  |
| GET | /features |  |
| GET | /prompt |  |
| GET | /object_info |  |
| GET | /object_info/{node_class} |  |
| GET | /api/jobs | List all jobs with filtering, sorting, and pagination. Query parameters: status: Filter by status (comma-separated): pending, in_progress, completed, failed workflow_id: Filter by workflow ID sort_by: Sort field: created_at (default), execution_duration sort_order: Sort direction: asc, desc (default) limit: Max items to return (positive integer) offset: Items to skip (non-negative integer, default 0) |
| GET | /api/jobs/{job_id} | Get a single job by ID. |
| GET | /history |  |
| GET | /history/{prompt_id} |  |
| GET | /queue |  |
| POST | /prompt |  |
| POST | /queue |  |
| POST | /interrupt |  |
| POST | /free |  |
| POST | /history |  |

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
