# Changelog

This changelog records repo-scoped milestones derived from actual git history.
It is intentionally selective: it tracks meaningful changes to docs, artifacts,
verification, workflow, and repo structure rather than every commit.

Repo version numbers describe repository and artifact-surface maturity. They do
not imply npm publication intent; `package.json` remains `private: true`.

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
