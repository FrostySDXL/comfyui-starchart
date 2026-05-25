---
name: Upstream Refresh
about: Track a pending upstream version refresh
title: "Upstream refresh available"
labels: ["upstream-watch"]
assignees: []
---

## Summary

The upstream watch workflow has detected that one or more pinned upstream versions may be outdated.

Use this maintainer-focused template only for version refresh follow-up. Use the
bug-report or docs-request template for normal contributor reports.

## Current Status

<!-- This section will be updated automatically by the upstream-watch workflow -->

## Next Actions

1. Review the upstream changelog for the newer version(s)
2. Run the suggested refresh command locally
3. Verify extracted output and run the full verification suite
4. Update `src/content/docs/reference/version-pin-status.md` with the new baseline
5. Close this issue once the refresh is merged

## Rollback

If the refresh introduces breaking changes, revert to the previous pinned snapshot and reopen this issue with notes.
