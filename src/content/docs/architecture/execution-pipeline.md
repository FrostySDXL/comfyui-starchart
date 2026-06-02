---
title: "Execution Pipeline"
---

**Evidence:** Source-backed from pinned snapshots
**Last Updated:** 2026-06-01
**Primary Sources:**
- `references/snapshots/2026-06-01/comfyui-core-v0.23.0/server.py` (v0.23.0, commit a88e02b18576283b1ff25a4b564548c5dc42cbf6)
- `references/snapshots/2026-06-01/comfyui-core-v0.23.0/execution.py` (v0.23.0, commit a88e02b18576283b1ff25a4b564548c5dc42cbf6)
**Baseline verification status:** Re-reviewed for core v0.23.0 / frontend v1.46.6 transition.

## Scope

This page documents the server-side execution pipeline that turns a submitted
prompt into queued work, live events, and stored history. It is an
architecture-level map of responsibilities and boundaries, not a step-by-step
API tutorial or a full engine internals reference.

## Pipeline Stages at a Glance

At the pinned `v0.23.0` baseline, prompt execution crosses a few distinct
stages:

1. request parsing in `POST /prompt`
2. prompt validation in `execution.validate_prompt(...)`
3. queue insertion on `self.prompt_queue`
4. prompt expansion into a `DynamicPrompt`
5. cache checks and execution scheduling through `ExecutionList`
6. node execution and progress/event delivery
7. history assembly for later lookup

Those stages are separate on purpose. Validation answers "is this graph safe to
run?" while execution answers "which work must actually happen right now?"

## Stage 1: Request Parsing and Prompt Preparation

`server.py` handles `POST /prompt` by reading JSON, applying prompt hooks, and
assigning queue priority.

The submitted `prompt` is already the API prompt graph at this boundary. Each
graph entry is keyed by node ID, names a `class_type`, and carries `inputs` that
may be literal values or linked-input pairs. Use [Prompt Submission](../api/prompt-submission.md)
for the request contract and extraction limits. Source-backed from pinned
snapshots: `references/snapshots/2026-06-01/comfyui-core-v0.23.0/server.py`
and `references/snapshots/2026-06-01/comfyui-core-v0.23.0/execution.py`.

- `number` controls explicit queue ordering when provided.
- `front: true` negates the generated queue number so the prompt runs earlier.
- `prompt_id` is caller-supplied when present, otherwise generated.
- `partial_execution_targets` narrows which output nodes should execute.

Before validation, the server also calls `self.node_replace_manager.apply_replacements(prompt)`.
That means the pipeline can rewrite node class usage before the validator and
executor see the final graph.

Prompt hooks run before validation and queue insertion, so they are the pipeline
surface for prompt-time inspection or normalization. WebSocket lifecycle events
start later, after queued work is picked up for execution. Source-backed from
pinned snapshots: `references/snapshots/2026-06-01/comfyui-core-v0.23.0/server.py`
and `references/snapshots/2026-06-01/comfyui-core-v0.23.0/execution.py`.

## Stage 2: Validation

Validation runs through `execution.validate_prompt(...)` before anything is put
on the queue.

The validator checks a few important boundaries:

- referenced node classes must exist
- linked outputs must match expected input types
- required inputs must be present
- literal values must satisfy min/max or combo constraints
- dependency cycles and inner-node validation failures surface as structured
  errors

This is why a prompt can fail fast with HTTP 400 and `node_errors` before any
real execution starts.

## Stage 3: Queue Insertion and Sensitive Metadata Handling

On validation success, the server builds a queue tuple and stores it on
`self.prompt_queue`.

The queued payload is intentionally split:

- public queue-visible data lives in `extra_data`
- sensitive keys listed in `execution.SENSITIVE_EXTRA_DATA_KEYS` are removed from
  that public copy and stored separately
- `create_time` is stamped into `extra_data` at queue time

That design explains why queue APIs are useful for scheduling and monitoring but
should not be treated as a full mirror of every original submission field.

## Stage 4: Execution Scheduling and Cache Checks

When a prompt starts, `PromptExecutor.execute_async(...)` creates a
`DynamicPrompt`, resets progress state, installs `WebUIProgressHandler`, and
prepares cache state.

Two scheduling ideas matter most:

- cache hits are detected before work runs, and reported through
  `execution_cached`
- actual execution order is managed by `ExecutionList`, not by naïve node-ID
  order

The pinned source therefore supports a topological, dependency-aware execution
model with caching layered into the scheduling path.

## Stage 5: Node Execution and Live Events

While the execution list is not empty, the executor stages one node at a time,
runs it, and either completes it, re-pends it, or stops on failure.

The live event surface is separate from the HTTP submission path:

- `execution_start` announces that work began
- `execution_cached` announces reused cached results
- `executing` reports non-cached node execution
- `progress` reports hook-backed progress counters when available
- `executed` forwards UI output when a node actually produced client-facing UI
- `execution_success`, `execution_error`, and `execution_interrupted` terminate
  the lifecycle

That split is why WebSocket monitoring complements the API but does not replace
queue and history lookup.

These lifecycle names are WebSocket-facing event types, not proof of a separate
Python callback hook for each transition. Use hook docs for extension timing and
the WebSocket page for event envelopes, targeting, and live state. Source-backed
from pinned snapshots: `references/snapshots/2026-06-01/comfyui-core-v0.23.0/server.py`
and `references/snapshots/2026-06-01/comfyui-core-v0.23.0/execution.py`.

## Stage 6: History Assembly

After execution finishes, the executor stores `outputs` and `meta` in
`self.history_result`. The history endpoints then expose that stored execution
record by `prompt_id`.

In practice, the pipeline publishes three different observation surfaces:

- queue state for current scheduling
- WebSocket events for live lifecycle visibility
- history records for stored post-run outputs

Each one answers a different question. None is a complete substitute for the
others.

## Failure Boundaries

The pinned source shows three important failure categories:

- validation failure before queueing
- execution failure after queue pickup
- interruption during execution

That distinction matters operationally because recovery paths differ. Validation
failures usually require prompt-shape fixes. Execution failures may require node
or runtime investigation. Interruptions reflect operator or control-plane
behavior rather than graph invalidity.

## What This Page Does Not Try to Do

This page does not:

- define every WebSocket payload in detail
- restate the full prompt request contract
- document every cache-provider internal
- guarantee undocumented execution-order behavior

Use it as the architecture map, then move to the narrower retained API pages for
exact contracts.

## Read Next

- [Architecture Overview](overview.md)
- [Prompt Submission](../api/prompt-submission.md)
- [WebSocket](../api/websocket.md)
- [History and Queue](../api/history-queue.md)
