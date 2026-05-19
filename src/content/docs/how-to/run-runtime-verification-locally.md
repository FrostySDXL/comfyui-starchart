---
title: "Run Runtime Verification Locally"
---

**Evidence:** Operational guidance
**Last Updated:** 2026-05-18
**Related:** `scripts/verify/runtime_smoke.py`, `scripts/extract/parse_from_api.py`, `scripts/verify/wait_for_runtime.py`

## Scope

Use this page when you want to run the repo's runtime smoke or runtime metadata
capture workflows against a live ComfyUI instance on your own machine or lab
environment.

This is a repo-local verification workflow. It does not redefine native ComfyUI
behavior, and it does not replace the canonical pinned artifact pipeline.

## Who This Page Is For

- maintainers verifying runtime-facing scripts against a live instance
- tooling authors who need optional runtime `object_info` capture
- contributors checking whether a live instance still matches repo expectations

## 1. Confirm the Runtime Is Reachable

Start with the smallest readiness check:

```bash
python scripts/verify/wait_for_runtime.py --url http://127.0.0.1:8188/features
```

Before state: you are not sure the instance is responding yet.
After state: the endpoint answers and you can proceed to a smoke or capture step.

## 2. Run the Smoke Check When You Want a Fast Runtime Sanity Pass

```bash
python scripts/verify/runtime_smoke.py --url http://127.0.0.1:8188
```

This checks a bounded runtime surface such as `/features`, `/system_stats`, and
`/object_info`. It is the right first step when you want confidence that the
instance responds like a ComfyUI server at all.

## 3. Capture Runtime Object Info When You Need Installed-Node State

```bash
python scripts/extract/parse_from_api.py \
  --url http://127.0.0.1:8188 \
  --version <version> \
  --commit <sha> \
  --output references/raw/object_info_runtime.json
```

Use this only when you need live runtime metadata. The output is instance
specific and is not part of the canonical published artifact contract.

## 4. Interpret the Outputs Correctly

- `runtime_smoke.py` proves a bounded live endpoint subset responded now
- `object_info_runtime.json` captures live installed-node state for that runtime
- neither output replaces the pinned canonical artifact baseline under
  `references/raw/`
- a passing smoke check does not prove image generation, model availability, or
  every custom node path

## 5. Stop or Continue Intentionally

Choose the next step based on what you are trying to prove:

- if you only needed runtime reachability, stop after the smoke pass
- if you needed live node metadata, keep the runtime capture and compare it with
  the pinned schema guidance
- if you are doing a broader refresh workflow, return to the repo's refresh and
  artifact publication sequence instead of treating runtime capture as closure by
  itself

## Read Next

- [Runtime and CI Operations](../reference/runtime-ci-operations.md)
- [Machine-Readable Artifacts](../reference/machine-readable-artifacts.md)
- [Object Info](../reference/object-info.md)
