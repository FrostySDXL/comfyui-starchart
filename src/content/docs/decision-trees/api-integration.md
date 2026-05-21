---
title: "Decision Tree: Choosing an Integration Approach"
---

**Last Updated:** 2026-05-21
**Evidence:** Source-backed from pinned snapshots
**Baseline verification status:** Verified against the current pinned baseline: core `v0.22.0`, frontend `v1.45.12`, snapshots `2026-05-21`.

## Overview

This page helps you decide the right integration approach for ComfyUI. Work
through the questions in order -- each answer leads to the approach that fits
your situation.

## Question 1: Where Does Your Code Run?

### My code runs outside ComfyUI (separate process, service, or script)

Go to Question 2.

### My code runs inside ComfyUI (Python on the server, or JS in the editor)

You need an **Extension**, not an API integration.

- If your code adds new graph-executable operations -> [Custom Node](../start-here/author.md)
- If your code adds new UI behavior or panels -> [Frontend Extension](../start-here/extension-developer.md)
- If your code adds new HTTP endpoints -> [Custom Routes](../how-to/add-custom-routes.md)
- If your code reacts to execution events -> [Server Hooks](../hooks/server-hooks.md)

---

## Question 2: Do You Need to Automate Workflow Execution?

### No -- I just want to embed ComfyUI in my application UI

Use the **ComfyUI client API only**. Load the ComfyUI iframe or embed the
frontend app. You do not need custom routes or server modifications.

Key APIs:

- [Prompt Submission](../api/prompt-submission.md) -- send workflows for execution
- [WebSocket](../api/websocket.md) -- track execution progress
- [History](../api/history-queue.md) -- fetch completed results

### Yes -- I want to drive workflow execution programmatically

Go to Question 3.

---

## Question 3: Do You Need Results Back From ComfyUI?

### No -- ComfyUI saves output to disk; I will poll the output directory

A **fire-and-forget** approach covers this:

```
POST /prompt  -->  get prompt_id  -->  monitor WebSocket for done  -->  read output dir
```

This is the simplest automation path. No custom routes needed.

### Yes -- I need structured data, intermediate results, or custom processing

Go to Question 4.

---

## Question 4: Do You Need Access to ComfyUI Internals (Model List, Queue State, Execution Data)?

### Yes -- I need access to runtime state that the API does not expose

Add **Custom Routes** inside ComfyUI. This gives you Python-level access to
ComfyUI internals and lets you expose exactly the data your integration needs.

- [Add Custom Routes](../how-to/add-custom-routes.md)
- [Server Hooks](../hooks/server-hooks.md) -- react to execution events from inside

Pattern: ComfyUI-Tooling-Nodes (`/api/etn/...` routes) is a community reference.

### No -- the standard API covers what I need

Use the **standard API surface**:

| What You Need | API Endpoint |
|--------------|-------------|
| Submit a workflow | `POST /prompt` |
| Track progress | WebSocket `/ws?clientId=...` |
| Fetch results | `GET /history/{prompt_id}` |
| List queue | `GET /queue` |
| Clear queue | `POST /queue` with `{"clear": true}` |
| Check node info | `GET /object_info` |
| Fetch/checkpoint a model | `GET /view` |

Complete route reference: [API Endpoints](../api/endpoints.md).

---

## Decision Summary

| Situation | Approach |
|-----------|----------|
| External script, automation, fire-and-forget | Standard API (`/prompt` + WebSocket) |
| External service, structured results needed | Standard API + optional custom routes |
| External tool, need runtime state | Custom Routes inside ComfyUI |
| Adding new graph operations | Custom Node |
| Adding new editor UI | Frontend Extension |
| Reacting to execution events from inside | Server Hooks |
| Complex tool with both UI and backend needs | Hybrid Extension |

## Combining Approaches

Real integrations often combine multiple approaches:

- Standard API for prompt submission and monitoring
- Custom Routes for model management or queue introspection
- Server Hooks for logging or side-effects during execution

[Extension Patterns](../extensions/patterns.md) covers architectural guidance for
combining these approaches.

## Constraints to Keep in Mind

- Custom nodes that depend on direct client-server coordination (shared memory,
  file watches, or non-HTTP IPC) do not work in pure API mode
- Backend validation can differ from what the frontend allows -- prefer
  explicit, narrow interfaces over flexible or wildcard inputs
- API mode does not support frontend hooks -- if your workflow needs
  frontend JS behavior, you cannot fully automate it via the API

## Read Next

- [API Endpoints](../api/endpoints.md)
- [Prompt Submission](../api/prompt-submission.md)
- [Start Here: Service Integration](../start-here/service-integration.md)
