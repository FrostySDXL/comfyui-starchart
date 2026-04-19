# Server.py Summary

**Last Synced:** 2026-04-19
**Source:** references\snapshots\2026-04-19\comfyui-core-v0.19.3\server.py

## Overview

Generated from `references/raw/server_endpoints.json`.

## Route Summary

| Method | Route | Description |
| --- | --- | --- |
| GET | /ws | WebSocket endpoint for real-time server-client communication. Supports status updates, execution progress, feature flag negotiation, and preview images. Query parameter: clientId (optional) - existing session ID to reuse |
| GET | / | Serves the ComfyUI frontend index.html with no-cache headers |
| GET | /embeddings | Lists all available embedding filenames (without extensions) from the embeddings folder |
| GET | /models | Lists all available model type folder names (e.g., checkpoints, Loras, VAEs) |
| GET | /models/{folder} | Lists all model files in a specific model type folder |
| GET | /extensions | Lists all JavaScript extension files from the web root and custom node EXTENSION_WEB_DIRS |
| POST | /upload/image | Uploads an image file to the input/output/temp directory. Supports subfolder organization and duplicate detection via hash comparison |
| POST | /upload/mask | Uploads a mask image and applies it as alpha channel to an existing output image referenced by original_ref |
| GET | /view | Views or downloads an image file from input/output directories. Supports preview generation, channel extraction (rgb/a), and asset hash resolution |
| GET | /view_metadata/{folder_name} | Extracts and returns the __metadata__ from a safetensors file header |
| GET | /system_stats | Returns system statistics including OS, RAM, VRAM, Python/PyTorch versions, and ComfyUI version info |
| GET | /features | Returns server-side feature flags for capability negotiation |
| GET | /prompt | Returns current prompt queue status information |
| GET | /object_info | Returns detailed information about all registered node types including inputs, outputs, categories, and metadata |
| GET | /object_info/{node_class} | Returns detailed information about a specific node type |
| GET | /api/jobs | List all jobs with filtering, sorting, and pagination. Query parameters: status: Filter by status (comma-separated): pending, in_progress, completed, failed workflow_id: Filter by workflow ID sort_by: Sort field: created_at (default), execution_duration sort_order: Sort direction: asc, desc (default) limit: Max items to return (positive integer) offset: Items to skip (non-negative integer, default 0) |
| GET | /api/jobs/{job_id} | Get a single job by ID. |
| GET | /history | Returns execution history (completed/failed prompts) with optional pagination |
| GET | /history/{prompt_id} | Returns history entry for a specific prompt ID |
| GET | /queue | Returns current prompt queue status with running and pending items |
| POST | /prompt | Submits a new prompt workflow for execution. Validates the prompt graph and adds it to the execution queue |
| POST | /queue | Manages the prompt queue - can clear all items or delete specific prompt IDs |
| POST | /interrupt | Interrupts currently running prompt processing. Can target specific prompt_id or do global interrupt |
| POST | /free | Sets flags to unload models and/or free VRAM after current prompt completes |
| POST | /history | Manages execution history - can clear all history or delete specific prompt IDs |

## Update Process

Regenerate this page after refreshing endpoint JSON.
