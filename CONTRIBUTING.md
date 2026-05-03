# Contributing

Thank you for contributing to the ComfyUI Knowledge Base. This guide covers everything you need to make changes safely and get them merged.

If you are new to documentation contributions, also read
[`docs/start-here/docs-contributor.md`](docs/start-here/docs-contributor.md)
for a gentler introduction to page modes and editorial standards.

`CONTRIBUTING.md` is the authoritative repo-local guide for maintainer-grade
workflows that are not fully duplicated in the published docs site.

---

## Quickstart

```bash
python -m pip install -r requirements.lock
python -m unittest discover -s tests -v
python -m mkdocs build
```

Serve locally: `python -m mkdocs serve`

### Dependency management

- The supported maintainer and CI install surface is `requirements.lock`.
- Edit direct dependencies in `requirements.in`.
- Do not hand-edit `requirements.lock`; regenerate it after direct dependency changes.
- `requirements.txt` remains only as a compatibility shim to `requirements.lock`.

Regenerate the lockfile from a Python 3.11+ environment with `pip-tools` installed:

```bash
python -m pip install pip-tools
python -m piptools compile --strip-extras requirements.in --output-file requirements.lock
```

The one-command wrapper for local verification:

```bash
python scripts/verify/run_all.py
```

Use `run_all.py` as the default maintainer-grade before-push check. It mirrors
the CI job's blocking checks in the same order. Advisory CI checks remain
separate, so you only need to run them locally when your change touches that
surface. The blocking path now includes artifact-integrity verification for the
canonical published JSON artifacts.

---

## What This Repository Is

This is a source-backed, version-pinned reference documentation project for
ComfyUI development. We extract facts from pinned upstream source snapshots,
not from memory. The repo publishes both human-readable documentation and
machine-readable JSON artifacts.

**Goals:** stable API reference, custom node patterns, extension architecture
guides, and tooling artifacts.

**Non-goals:** official docs replacement, community wiki, package registry.

---

## Repository Map

| Path | What lives here | Can you edit it by hand? |
|------|-----------------|--------------------------|
| `docs/` | MkDocs pages (reference, tutorials, decision guides) | **Yes** -- this is the main human contribution surface |
| `examples/` | Hand-authored pattern examples, API calls, workflows | **Yes** |
| `references/raw/` | Extracted JSON from upstream snapshots (endpoints, hooks, schemas) | **No** -- edit upstream snapshots in `references/snapshots/`, then re-run extractors |
| `references/community/` | Human-editable metadata for community pages and ecosystem packages | **Yes** -- edit JSON directly, then regenerate downstream artifacts |
| `references/snapshots/` | Pinned upstream source files organized by date | **No** -- these are vendored upstream source. Update them with `scripts/refresh_snapshots.py`, not by hand. |
| `scripts/extract/` | Scripts that parse source into JSON | **Yes** -- if you are adding or fixing an extractor |
| `scripts/generate/` | Scripts that render markdown from JSON | **Yes** -- if you are adding or fixing a generator |
| `scripts/verify/` | Validation scripts (blocking and non-blocking) | **Yes** -- if you are adding or fixing a verifier |
| `tests/unit/` | Unit tests for scripts | **Yes** -- every new script needs tests |
| `docs/artifacts/` | Published JSON artifacts and manifest | **No** -- produced by `scripts/generate/publish_reference_artifacts.py` |
| `docs/ecosystem/map.md` | Generated community ecosystem page | **No** -- edit `references/community/ecosystem_packages.json`, then regenerate |
| `.github/workflows/` | CI and deployment automation | **Yes** -- but test locally first |


## Decision Tree: What Should I Do?

| I want to... | Start by reading... | Edit these files... | Run these checks... |
|--------------|---------------------|---------------------|---------------------|
| Fix or add a docs page | The target page + `docs/reference/source-evidence-policy.md` + `docs/reference/writing-style-guide.md` | `docs/<topic>/<page>.md`; use `templates/docs/` or `scripts/new_doc.py` | `python scripts/verify/cross_references.py` + `python -m mkdocs build` |
| Update the community catalog | `references/community/ecosystem_packages.json` + `docs/reference/community-maintenance-policy.md` | The JSON source file | `validate_schema.py`, `community_metadata.py`, `community_staleness.py`, `generate_community_pages.py`, `community_generated_freshness.py`, `community_page_coverage.py`, `cross_references.py`, `mkdocs build` |
| Update extracted references after a snapshot refresh | Matching extractor in `scripts/extract/` + snapshot files in `references/snapshots/<date>/` | Run the extractor script | `python scripts/verify/extraction_idempotency.py` + `validate_schema.py` |
| Add a new extractor | An existing extractor in `scripts/extract/` + its test in `tests/unit/` | New script + new test | `python -m unittest discover -s tests -v` |
| Add a verification script | An existing verifier in `scripts/verify/` + its test in `tests/unit/` | New script + new test + update `run_all.py` / `.github/workflows/ci.yml` intentionally | `python -m unittest discover -s tests -v` |
| Refresh upstream to a new version | `scripts/refresh_snapshots.py` | Back up `references/raw/`, run refresh, republish artifacts, then regenerate the delta summary when comparing baselines | `publish_reference_artifacts.py` + `generate_snapshot_delta_summary.py` + `run_all.py` |
| Change CI behavior | Relevant workflow in `.github/workflows/` + adjacent operational docs | Edit YAML + linked docs | Inspect YAML carefully, run `python -m unittest discover -s tests -v -p "test_run_all.py"` and `python scripts/verify/run_all.py`, then inspect the Actions tab after push |


## Task Playbooks

### Editing Prose Documentation

1. **Read the target page** and the pages it links to or from.
2. **Read the policy files** before changing evidence labels, tone, or structure:
   - `docs/reference/source-evidence-policy.md`
   - `docs/reference/writing-style-guide.md`
   - `docs/reference/doc-quality-checklist.md`
3. **Edit the page.** Keep claims tied to sources from `references/snapshots/` or
   `docs.comfy.org`. Do not write from memory.
4. **For new pages**, copy the matching template from `templates/docs/` (choose from `scaffold`, `tutorial`, `reference`, `decision-guide`, or `community-pattern`) or run:
   ```bash
   python scripts/new_doc.py --output docs/how-to/my-topic.md --mode tutorial --title "My Topic"
   ```
5. **Verify locally:**
   ```bash
   python scripts/verify/cross_references.py
   python -m mkdocs build
   ```
6. **Review your diff** before committing. Ensure you did not accidentally edit
   generated files.

### Updating the Community Catalog

The ecosystem map at `docs/ecosystem/map.md` is generated. Do not edit it by hand.

1. Edit `references/community/ecosystem_packages.json` for catalog entries.
2. Edit `references/community/community_pages.json` for page review metadata.
3. Run the verification and generation pipeline in order:
   ```bash
   python scripts/verify/validate_schema.py
   python scripts/verify/community_metadata.py
   python scripts/verify/community_staleness.py
   python scripts/generate/generate_community_pages.py
   python scripts/verify/community_generated_freshness.py
   python scripts/verify/community_page_coverage.py
   python scripts/verify/cross_references.py
   python -m mkdocs build
   ```
   Each step validates a different layer: schema correctness, metadata rules,
   staleness, regeneration, freshness, coverage, cross-links, and final build.

### Updating Extracted References

1. Place or update upstream source files in `references/snapshots/<date>/`.
   Alternatively, run:
   ```bash
   python scripts/refresh_snapshots.py --core-version <version>
   ```
2. Run the matching extractor with `--version` and `--commit` flags:
   ```bash
   python scripts/extract/parse_server.py <path> --version <v> --commit <sha>
   python scripts/extract/parse_hooks.py <paths...> --version <v> --commit <sha>
   python scripts/extract/parse_node_api_schema.py <server> <io> <types> --version <v> --commit <sha>
   ```
3. Optionally enrich with runtime data from a live ComfyUI instance:
   ```bash
   python scripts/extract/parse_from_api.py --url <url> --version <v> --commit <sha> --output references/raw/object_info_runtime.json
   ```
4. Regenerate markdown:
   ```bash
   python scripts/generate/md_from_json.py
   ```
5. Verify:
   ```bash
   python scripts/verify/cross_references.py
   python scripts/verify/validate_schema.py
   python scripts/verify/extraction_idempotency.py
   ```

### Refreshing Upstream Baselines

Use this when you are proving or updating the pinned baseline rather than rerunning a single extractor.

1. Preserve the current canonical artifacts before refresh:
   ```bash
   Copy-Item -Recurse references/raw references/raw_backup_before_refresh
   ```
2. Run the refresh pipeline:
   ```bash
   python scripts/refresh_snapshots.py --core-version <version> --frontend-version <version>
   ```
3. Republish the artifact surface:
   ```bash
   python scripts/generate/publish_reference_artifacts.py
   ```
4. Verify canonical raw artifacts still match the published current copies and
   manifest checksums:
   ```bash
   python scripts/verify/verify_artifact_integrity.py
   ```
5. If you are comparing two baselines, generate the published delta summary from the preserved copy:
   ```bash
   python scripts/generate/generate_snapshot_delta_summary.py --old references/raw_backup_before_refresh --new references/raw --output docs/artifacts/delta-summary.json
   ```
6. Remove the temporary backup after confirming the delta output.
7. Run the maintainer verification gate:
   ```bash
   python scripts/verify/run_all.py
   ```

### Adding a New Verification Script

1. Create `scripts/verify/<name>.py`.
   - Exit `0` on pass, exit `1` on fail.
   - Print human-readable error messages.
2. Add tests in `tests/unit/test_<name>.py`.
   - Include at minimum: import check, smoke test, edge cases.
3. Add it to `scripts/verify/run_all.py` if it should be part of the default
   local blocking gate before push.
4. Add the script to `.github/workflows/ci.yml` if it should run in CI.
5. Choose CI placement intentionally:
   - **Blocking:** add it to the main CI sequence when failure should stop merge
     and maintainers should normally catch it locally through `run_all.py`.
   - **Advisory:** add it with `continue-on-error: true` when the signal is
     useful but still needs human follow-up or is expected to be noisy.
6. Treat this section as the authoritative home for future verifier placement.
7. Run the full test suite:
   ```bash
   python -m unittest discover -s tests -v
   ```

### Adding a New Extractor

1. Create `scripts/extract/<name>.py`.
   - Read source from `references/snapshots/`.
   - Write JSON to `references/raw/`.
   - Include `--version` and `--commit` flags in output metadata.
   - Normalize all paths to forward slashes in JSON output.
2. Add tests in `tests/unit/`.
3. Add a generator in `scripts/generate/` if markdown output is needed.
4. Run tests and verify the pipeline end-to-end.

---

## Generated vs Hand-Authored Boundaries

Understanding this boundary prevents accidentally editing files that will be overwritten later.

- **Hand-authored:** Pages under `docs/`, files under `examples/`, and editorial reference files.
- **Generated:** `docs/ecosystem/map.md` is produced by `scripts/generate/generate_community_pages.py` from `references/community/ecosystem_packages.json`.
- **Extracted:** JSON files under `references/raw/` are produced by `scripts/extract/` from `references/snapshots/`.
- **Published:** Files under `docs/artifacts/` are produced by `scripts/generate/publish_reference_artifacts.py`.

If a file is generated or extracted, change its source and rerun the pipeline rather than editing the output directly.

---

## Conventions

- **Source citations required:** Do not claim official ComfyUI behavior without a citation from `references/snapshots/` or `docs.comfy.org`.
- **No emojis or emoticons** in any file.
- **Forward slashes only** in JSON metadata paths. If you run extractors on Windows, ensure paths are normalized.
- **Run verification before opening a PR.** Do not rely on CI to catch issues you could have found locally.
- **Prefer small, verifiable changes.** Large diffs are harder to review and more likely to introduce errors.

---

## Verification Commands Reference

Run the narrowest relevant checks first while iterating, then
`python scripts/verify/run_all.py` before opening a PR or handing maintainer
workflow changes to review. The wrapper mirrors the CI job's blocking checks;
advisory checks remain separate.

### Essential (run these for almost every change)

```bash
python scripts/verify/cross_references.py
python scripts/verify/verify_artifact_integrity.py
python -m mkdocs build
python -m unittest discover -s tests -v
```

### Community catalog changes

```bash
python scripts/verify/validate_schema.py
python scripts/verify/community_metadata.py
python scripts/verify/community_staleness.py
python scripts/generate/generate_community_pages.py
python scripts/verify/community_generated_freshness.py
python scripts/verify/community_page_coverage.py
python scripts/verify/cross_references.py
python -m mkdocs build
```

### Full local verification

```bash
python scripts/verify/run_all.py
```

This is the recommended maintainer pre-push command.

### Individual verifiers

Scripts marked **[BLOCKING]** will fail CI and prevent merge. Scripts marked
**[non-blocking]** run in CI but do not stop the pipeline.

```bash
python scripts/verify/cross_references.py              # [BLOCKING]
python scripts/verify/validate_schema.py               # [BLOCKING]
python scripts/verify/verify_artifact_integrity.py     # [BLOCKING]
python scripts/verify/community_generated_freshness.py # [BLOCKING]
python scripts/verify/community_page_coverage.py       # [BLOCKING]
python scripts/verify/stale_content.py                 # [non-blocking]
python scripts/verify/extraction_idempotency.py        # [non-blocking]
python scripts/verify/upstream_pins.py                 # [non-blocking]
python scripts/verify/community_metadata.py            # [non-blocking]
python scripts/verify/community_staleness.py           # [non-blocking]
```

### Generators

```bash
python scripts/generate/md_from_json.py
python scripts/generate/generate_community_pages.py
python scripts/generate/publish_reference_artifacts.py
python scripts/generate/generate_snapshot_delta_summary.py --old <dir> --new <dir> --output docs/artifacts/delta-summary.json
```

When generating a refresh delta from the live repo state, `--old` should point at a preserved pre-refresh copy of `references/raw/` because `refresh_snapshots.py` overwrites the canonical raw artifacts in place.

### Runtime testing (optional)

If you have a live ComfyUI instance available, you can optionally validate
against a real server:

```bash
python scripts/verify/runtime_smoke.py --url http://127.0.0.1:8188
python scripts/verify/wait_for_runtime.py --url http://127.0.0.1:8188/object_info
```

These are not required for most contributions, but are useful when adding or
modifying runtime extractors.

### When verification fails

- **`validate_schema.py` fails:** The error message usually names the exact file
  and field that is invalid. Fix the source JSON, not any generated output.
- **`cross_references.py` fails:** It lists broken internal links. Check that the
  target page exists and that the path uses forward slashes.
- **`verify_artifact_integrity.py` fails:** A canonical raw artifact,
  published current copy, or manifest checksum is out of sync. Republish with
  `publish_reference_artifacts.py` and verify that no published copy was
  hand-edited.
- **`community_generated_freshness.py` fails:** You edited a community JSON file
  but forgot to rerun `generate_community_pages.py` before verifying.
- **`extraction_idempotency.py` fails:** See the Common Pitfalls note on
  idempotency drift.

Always fix the root cause rather than bypassing the check.

---

## Common Pitfalls

- **Editing generated markdown directly:** `docs/ecosystem/map.md` looks like a normal markdown file, but it is produced by a generator. Always edit `references/community/ecosystem_packages.json` and rerun the generator instead.
- **Windows backslashes in JSON:** If you author or run extractors on Windows, paths written with `str(path)` will contain backslashes. Always normalize with `.replace("\\", "/")` before writing JSON metadata.
- **Forgetting to regenerate after JSON changes:** If you edit `references/raw/` or `references/community/` JSON files, rerun the matching generator before running `cross_references.py` or `mkdocs build`.
- **Misunderstanding CI blocking behavior:** `cross_references.py`, `validate_schema.py`, `verify_artifact_integrity.py`, `community_generated_freshness.py`, and `community_page_coverage.py` will block CI and prevent merge. `stale_content.py`, `extraction_idempotency.py`, `upstream_pins.py`, `community_metadata.py`, and `community_staleness.py` run in CI but do not block the pipeline.
- **Misreading semantic enrichment fields:** Plan K adds `traceability` markers and richer typed detail to endpoints, hooks, and node schema fields. These are best-effort from static analysis. The `kind` field is reliable; deeper fields should be treated as helpful signals, not strict runtime contracts.
- **Writing from memory:** Claims about ComfyUI behavior must be traceable to a pinned snapshot or official docs. If you cannot find a source, mark the claim accordingly or leave it out.
- **Skipping unit tests for script changes:** If you change any script under `scripts/`, add or update the matching test under `tests/unit/` and run the full test suite.
- **Misreading extraction idempotency failures:** The idempotency checker may report byte-level differences because extractors write timestamps (`extracted_date`). These are expected. Structural differences in the JSON are the real concern.

---

## Pull Request Checklist

Before opening a PR, confirm the following:

- [ ] **The change is scoped:** one logical change per PR (docs fix, catalog update, new script, etc.)
- [ ] **Generated files were not hand-edited:** verify with `git diff --name-only` that you are not modifying generated outputs without changing their sources
- [ ] **Verification passes:** the relevant checks from the Decision Tree above exit `0`
- [ ] **Tests pass:** `python -m unittest discover -s tests -v` exits cleanly (required for script changes; recommended for docs changes)
- [ ] **Docs build:** `python -m mkdocs build` completes without errors
- [ ] **Evidence labels are correct:** docs pages have the right evidence label per `source-evidence-policy.md`
- [ ] **Style matches conventions:** page mode, tone, and structure follow `writing-style-guide.md`
- [ ] **Cross-links are intentional:** links resolve to real pages; "Read Next" blocks contain deliberate next steps

For script or extractor changes, also include:
- [ ] **The exact command you ran** and its output in the PR description
- [ ] **A test** covering the new behavior in `tests/unit/`

---

## Getting Help

- Read `docs/start-here/docs-contributor.md` for an introduction to editorial standards.
- Read `docs/reference/writing-style-guide.md` for page modes and tone.
- Read `docs/reference/source-evidence-policy.md` for trust hierarchy and evidence labeling.
- Read `docs/reference/doc-quality-checklist.md` for a pre-submit review step.
- Review `AGENTS.md` for the full operational reference (machine-oriented, but comprehensive).
