# Known Limitations

**Status:** Scaffold -- requires active curation from maintainers

## Purpose

This section documents tribal knowledge about ComfyUI limitations and their
workarounds. The goal is to capture what lives in Discord threads and archived
issues so it does not disappear.

## Curation Policy

This section is a **scaffold that requires active curation**. A limitation
documented here without validation will become stale and potentially mislead
readers. Before adding an entry:

1. **Verify** the limitation exists in the current ComfyUI version
2. **Confirm** the workaround is effective and does not break other behavior
3. **Cite** a source: official docs, upstream source, or a maintained community
   discussion (GitHub issue, Discord with maintainer participation)
4. **Date** the entry so readers know how fresh the information is

If you cannot verify a limitation with a source, do not add it. It is better
to have no entry than a misleading one.

## Categories

### API and Execution Limitations

Limitations that affect API-mode use, automation, and server-side behavior.
No verified entries yet -- see curation policy above.

### Frontend and Editor Limitations

Limitations that affect the ComfyUI editor, canvas behavior, or frontend
extensions. No verified entries yet -- see curation policy above.

### Custom Node Limitations

Limitations that affect custom node authors, V1/V3 compatibility, or
packaging. No verified entries yet -- see curation policy above.

### Community Package Limitations

Known issues with popular community packages that are effectively
unmaintained or have design decisions that cause problems. No verified
entries yet -- see curation policy above.

## Adding an Entry

When adding an entry, use this template:

```markdown
### Limitation Title

**Source:** [citation or "unverified -- community report"]

**Affected versions:** [version range or "current"]

**Description:** [clear description of the limitation]

**Workaround:** [if one exists, with caveats]
```

## Scope

This section does not cover:

- upstream bugs that are actively being fixed (watch the ComfyUI GitHub issues)
- personal workflow design choices
- GPU or hardware-specific issues
- community package features (those belong in the ecosystem map)

## Maintenance

This section needs a designated curator who:

- verifies entries periodically against newer ComfyUI versions
- removes entries when limitations are fixed
- updates workarounds when they break in newer versions
- validates new entries before they are added
