---
title: "Known Limitations: Extension Boundaries"
---

**Evidence:** Official docs-backed from docs.comfy.org
**Last Updated:** 2026-05-18

## Scope

This page groups limitations that come from the extension and distribution
boundary: Manager behavior, registry-backed install flows, and cleanup
assumptions for packaged extensions.

## New Manager UI does not support arbitrary git URL installs

**Source:** https://docs.comfy.org/manager/pack-management

**Verified in:** docs.comfy.org Manager new UI documentation

**Status:** Behavioral constraint

**Description:** The official Manager new UI only supports installing node packs
that are available through the registry-backed flow. The same docs state that
the new UI does not offer git-based installation.

**Workaround:** Register the package through the supported Manager and registry
flow if you want it to appear in the new UI. Otherwise document manual install
steps separately instead of implying users can paste an arbitrary git URL into
the new Manager interface.

**Last verified:** 2026-04-22

---

## `uninstall.py` is not a guaranteed cleanup path

**Source:** https://docs.comfy.org/custom-nodes/backend/manager

**Verified in:** docs.comfy.org Manager publication documentation

**Status:** Behavioral constraint

**Description:** The official Manager publication docs list `uninstall.py` as
an optional lifecycle script and explicitly warn that users can delete the
directory directly. That means authors cannot rely on `uninstall.py` as the
only cleanup path for critical state.

**Workaround:** Treat `uninstall.py` as best-effort cleanup only. Keep critical
state inside the package directory when possible, or make cleanup idempotent and
recoverable if the directory is removed without running the script.

**Last verified:** 2026-04-22

## Read Next

- [Known Limitations](index.md)
- [Integrate with Manager](../how-to/integrate-with-manager.md)
- [Extension Points](../hooks/extension-points.md)
