# Changelog

This changelog records repo-scoped milestones derived from actual git history.
It is intentionally selective: it tracks meaningful changes to docs, artifacts,
verification, workflow, and repo structure rather than every commit.

Repo version numbers describe repository and artifact-surface maturity. They do
not imply npm publication intent; `package.json` remains `private: true`.

## 2026-05-25 - maintainer refactors and refresh hardening

### Maintainer tooling structure

- Split `scripts/refresh_snapshots.py` into focused helper modules under
  `scripts/common/` while preserving the existing script entrypoints and wrapper
  surface.
- Split `scripts/extract/parse_server.py` into focused helper modules for block
  scanning, helper-body extraction, parameter inference, and return inference.
- Extract published-schema validation into
  `scripts/verify/published_schema_validation.py` and keep
  `schema_common.py`/`validate_schema.py` compatibility surfaces intact.

### Verification and tests

- Add targeted unit coverage for the new refresh, server-extractor, helper, and
  published-schema validation boundaries.
- Harden refresh failure handling so snapshot refresh exits cleanly when the
  delegated refresh step raises a runtime error.

### Maintainer guidance and published artifact docs

- Refresh `AGENTS.md`, `CONTRIBUTING.md`, and
  `reference/machine-readable-artifacts.md` so maintainer workflow guidance,
  follow-up commands, and merged docs-index support-artifact behavior match the
  implemented repo surface.

## 2026-05-24 - docs surface reduction and support-surface reconciliation

### Published docs surface

- Reduce the published docs tree to the retained 30-page surface and prune the
  removed routing, tutorial, troubleshooting, ecosystem, and legacy pages.
- Follow-up commit `d01f978` then removed
  `reference/doc-quality-checklist.md`, producing the current retained 29-page
  surface.
- Add `start-here/artifact-consumer.md` and `reference/topic-scope.md` as the
  new retained entry points for artifact consumers and published-surface scope
  policy.
- Rewrite retained start-here, architecture, API, hooks, custom-node, and
  reference pages so they no longer route readers to deleted docs.

### Navigation, artifacts, and metadata

- Reduce `src/site/sidebar-data.json` to the retained surface and regenerate the
  merged `docs-index.json` support artifact to match it.
- Merge `docs-index.json` and `tooling-index.json` into a single support index
  under `public/artifacts/docs-index.json`. The merged schema
  (`docs-index.schema.json` v1.1.0) tightens `additionalProperties` from `true`
  to `false` at root, scope, page, and the new `tooling_metadata` level to match
  the former tooling-index strictness. Downstream consumers that previously
  attached custom keys to page entries will need to adjust to the stricter
  contract.
- Prune `references/community/community_pages.json` so community tracking now
  matches the reduced published surface.
- Prune and retarget `references/tooling-index-metadata.json` so tooling routing
  no longer references deleted docs paths such as `api/client-id.md`.

### Verification, tests, and repo-local guidance

- Update `community_generated_freshness.py` so it passes cleanly when no
  generated community page is currently tracked on the published surface.
- Update affected unit tests and Node sidebar tests to reflect the reduced
  navigation and the new artifact-consumer routing path.
- Clean up repo-local guidance and example READMEs so contributor and consumer
  entry points no longer link to deleted docs pages.

## 2026-05-21 - packaging follow-up, generator refresh, and agent-facing guidance

### Packaging, imports, and verification architecture

- Package the maintainer script surface via `pyproject.toml`, add package marker
  files under `scripts/`, and remove the remaining `sys.path` import hacks.
- Split schema validation into dedicated modules under `scripts/verify/` while
  preserving `validate_schema.py` as the compatibility CLI entrypoint.
- Add shared script helpers and targeted unit coverage for the new packaging and
  validator layout.

### Pinned baseline and artifacts

- Refresh the pinned baseline to ComfyUI core `v0.22.0` and frontend `v1.45.12`.
- Regenerate published artifacts and update version-pin history.
- Normalize delta-summary comparison to suppress provenance-only path churn in node schema comparisons.

### CI, dependency, and maintainer workflow updates

- Add `.python-version`, move maintainer tooling metadata into
  `pyproject.toml`, add advisory `mypy`, and regenerate `requirements.lock`.
- Update CI to use pip caching and keep the advisory typing pass in the
  supplemental verification lane.
- Refresh `AGENTS.md` and `CONTRIBUTING.md` so packaging, verification, and
  upstream-watch guidance matches the implemented maintainer workflow.

### Documentation remediation and repo orientation

- Fix stale docs examples and baseline-status wording across the targeted docs
  surface, including queue-clear guidance, V3 node examples, glossary routing,
  and mixed-evidence style guidance.
- Condense and reposition the root `README.md` so it routes humans and agents to
  the right docs, artifact, and maintainer entry points more directly.

## 2026-05-20 - verifier maintenance and docs-surface boundaries

### Maintainer guidance and history surfaces

- Clarify in `AGENTS.md` and `CONTRIBUTING.md` that `CHANGELOG.md` is the
  canonical chronological repo-history surface while
  `src/content/docs/whats-new/index.md` stays a short curated highlights page.
- Document the current Astro/Starlight `Entry docs → 404 was not found.` build
  message as benign noise unless the build fails or `dist/404.html` is missing.

### Verification and test coverage

- Align blocking-verifier inventories with the actual CI and `run_all.py`
  surfaces, including `sidebar_navigation_coverage.py` and
  `rendered_links.py`.
- Add dedicated unit and CLI coverage for `sidebar_navigation_coverage.py`.
- Keep `rendered_links.py` fixture coverage in its dedicated test module rather
  than duplicating it in the shared verifier smoke tests.

### Reader-facing highlights

- Update `src/content/docs/whats-new/index.md` so its verification notes match
  current CI behavior and explicitly point maintainers to `CHANGELOG.md` for
  exhaustive repo history.

## 2026-05-20 - repo rename to ComfyUI StarChart

### Repo identity and hosting

- Rename the repository identity from ComfyUI Knowledge Base to ComfyUI
  StarChart across the primary brand, package, and hosting surfaces.
- Align the Astro site URL, GitHub Pages base path, and GitHub repository link
  with the new `comfyui-starchart` slug.

### Docs, examples, and support artifacts

- Update the docs home title, top-level repo guidance, published schema titles,
  and consumer example base-URL conventions to the new name.
- Regenerate `public/artifacts/docs-index.json` so the published docs-discovery
  support artifact reflects the renamed docs home.

### Verification and routing

- Update repo-local link-rewrite and rendered-link verification base-path
  constants and tests so build-time routing checks follow the new Pages path.

## 0.2.0 - 2026-05-19

### Repo metadata

- Raise the repo version signal from `0.0.1` to `0.2.0` so the root metadata better reflects the current maturity of the docs, artifact, and verification surface.

### Docs and examples

- Add a Deep Dives hub page and route it from the sidebar.
- Add a snapshots README for contributor orientation.
- Document versioned artifact retention separately from temporary refresh
  backups.
- Expand the examples surface with workflow, route-registration, and
  delta-summary consumer starter patterns.

## 2026-05-19 - workflow, provenance, and delta trust hardening

### Workflow and maintenance

- Relocate refresh backup working state under `references/_refresh_backups/` and
  align refresh provenance follow-up commands with the new path.
- Harden maintainer workflow documentation around refresh closure, rollback, and
  durable versus temporary artifact history.

### Docs provenance

- Refresh baseline-status wording across the docs surface so stale or partially
  re-reviewed pages no longer imply stronger verification than actually
  happened.

### Verification and artifacts

- Normalize delta-summary hook comparisons so snapshot-path provenance noise does
  not appear as semantic JS hook drift.
- Expand Node-side utility coverage and regenerate the published delta summary.

## 2026-05-18 - baseline refresh and CI hardening

### Pinned baseline and artifacts

- Refresh the pinned baseline to ComfyUI core `v0.21.1` and frontend `v1.45.9`.
- Regenerate published artifacts and update version-pin history.

### CI and verification

- Align Node.js workflow handling with `.nvmrc` and raise the site/framework
  baseline to Node.js 24.
- Tighten verification, refresh support, and repo hygiene around cross-platform
  paths and workflow safety.

### Docs surface

- Expand guidance, navigation, and deep-dive content around official system
  docs, hooks, and tooling boundaries.

## 2026-05-17 - site-platform migration and docs cleanup

### Site platform

- Migrate the documentation build from MkDocs to Astro Starlight, establishing
  the current site framework, navigation model, and frontend build surface.
- Fix site tracking so `src/site/` assets stay versioned after the migration
  rather than being masked by a root-anchoring gitignore issue.

### Docs cleanup after migration

- Remove stale docs fallbacks and duplicated title H1 patterns left over from
  the pre-Starlight surface.
- Fix lingering MkDocs references and ambiguous path wording so maintainer and
  reader guidance matches the new site stack.
- Apply full-repo review findings to stabilize the migrated site surface.

## 2026-05-13 - docs routing and example-surface growth

### Docs and guidance

- Add official system deep dives and bounded tooling architecture guidance.
- Expand hooks, subgraph guidance, and operational how-to coverage.

### Examples and verification

- Add an example-surface integrity verifier and keep it advisory while the
  examples surface continues to grow.

## 2026-05-03 - published artifact and routing foundation

### Published artifact surface

- Add schema publication, artifact integrity verification, and docs-index
  freshness checks.
- Publish manifest-backed current/versioned artifact copies and harden artifact
  contract guidance.

### Navigation and authoring

- Regroup docs entry paths, add routing hubs and glossary coverage, and harden
  doc bootstrap workflow.

## 2026-04-24 - starter examples and packaged artifacts

### Examples and consumers

- Add starter artifact-consumer examples and route-backed extension examples.
- Add runtime CI operations guidance and expand contributor onboarding.

### Artifact packaging

- Add the artifact packaging pipeline and docs-discovery support surfaces.

## 2026-04-19 - initial pinned reference baseline

### Repo scaffold

- Create the initial knowledge-base scaffold.
- Pin the first upstream source snapshot baseline.
- Add initial source-backed docs, evidence policy, cross-reference checks, and
  maintainer verification basics.
