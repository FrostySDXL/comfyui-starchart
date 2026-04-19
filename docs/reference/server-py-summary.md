# Server.py Summary

**Last Synced:** 2026-04-19
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

## Update Process

Regenerate this page after refreshing endpoint JSON.
