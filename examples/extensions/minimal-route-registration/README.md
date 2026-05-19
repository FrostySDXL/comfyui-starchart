# Minimal Route Registration Example

**Status:** Starter pattern

## What This Example Shows

This directory isolates the smallest server-side route-registration pattern this
repo recommends showing in examples:

1. get `PromptServer.instance`
2. guard against duplicate registration
3. register one extension-owned route on `PromptServer.instance.routes`
4. return a small JSON response that proves the route is live

## Files

- `routes.py` - minimal idempotent route registration helper

## What This Proves

- a bounded extension can register custom HTTP routes without mixing in custom
  nodes or frontend code
- idempotency guards belong in repo examples so repeated imports do not silently
  duplicate route handlers

## What This Intentionally Leaves Out

- package import wiring
- custom-node registration
- frontend panels, commands, or hooks
- persistence, authentication, or production deployment concerns

Use this as the smallest route surface reference. For broader composition
patterns, compare it with
[`examples/extensions/hybrid-v1-route/`](../hybrid-v1-route/README.md) and the
published how-to pages for custom routes and server extension boundaries.
