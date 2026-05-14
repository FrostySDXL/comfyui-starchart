# Hooks Section Guide

**Evidence:** Operational guidance
**Last Updated:** 2026-05-13

## Scope

This hub routes readers through ComfyUI hook and extension-boundary pages.
Start here when you know you need an extension surface but have not yet picked
the right layer.

## Read First

- [Extension Points](extension-points.md) if you are still choosing the surface
- [JavaScript Hooks](javascript-hooks.md) for frontend and editor behavior
- [Server Hooks](server-hooks.md) for the narrow Python callback and event-boundary surface

## Choose by job

| Goal | Page | Why this page first |
|------|------|---------------------|
| Patch node UI, menus, workflow-load behavior, or editor lifecycle | [JavaScript Hooks](javascript-hooks.md) | Covers the supported frontend hook surface and when to choose each hook |
| Inspect prompt submissions or understand the limited Python callback/event surface | [Server Hooks](server-hooks.md) | Keeps the server-side trust boundary explicit instead of implying a large hook catalog |
| Decide between hooks, routes, messages, or custom nodes | [Extension Points](extension-points.md) | Acts as the chooser page for layer selection |
| Work on advanced subgraph traversal, identifier, or widget-promotion behavior | [Subgraph Extension Behavior](subgraph-extension-behavior.md) | Advanced graph/UI cases belong on the dedicated subgraph page |

## Section roles

- Use this page to route.
- Use the body pages for the actual details.
- Do not treat the hooks section as one universal plugin API. The pages here
  keep JavaScript hooks, server callbacks, routes, messages, and custom nodes
  intentionally separate.
