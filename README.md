# ComfyUI StarChart

**Last Updated:** 2026-06-26
**ComfyUI Version Pin:** Core `v0.26.0` (`f6c162ddcfbd7eefb39c06fe5b8d4c46e8d09f40`) with official frontend `v1.47.5` (`e604c85b88cc3eb5f6c07063aba2cbb536fd8e85`) for the current pinned snapshots and extracted reference data

**Evidence:** Operational guidance

ComfyUI StarChart is a pinned, source-backed ComfyUI developer fact layer for
tools, agents, integrations, and version-aware developers.

- Hosted docs: <https://frostysdxl.github.io/comfyui-starchart/>
- Artifact manifest: <https://frostysdxl.github.io/comfyui-starchart/artifacts/manifest.json>
- Current server endpoints: <https://frostysdxl.github.io/comfyui-starchart/artifacts/current/server_endpoints.json>
- Current JavaScript hooks: <https://frostysdxl.github.io/comfyui-starchart/artifacts/current/js_hooks.json>

Use StarChart when you need to:

- check whether a ComfyUI route, hook, schema surface, or WebSocket event exists
  in the pinned baseline
- give an agent bounded ComfyUI development context without scraping scattered
  web sources
- build integration or CI tooling against versioned JSON artifacts with schemas
  and checksums
- compare current pinned facts with retained source snapshots and published delta
  summaries

## Use StarChart in 3 Minutes

To consume the hosted artifacts without cloning, start from the manifest URL:

```text
https://frostysdxl.github.io/comfyui-starchart/artifacts/manifest.json
```

Then load the canonical current artifact URL from the manifest and validate the
downloaded bytes against its `sha256` before using the artifact in strict
tooling.

After cloning the repo, run the no-runtime demo without building the site or
starting ComfyUI:

```bash
python examples/consumers/three-minute-artifact-reader/read_starchart.py
```

The demo reads the checked-in `public/artifacts/manifest.json` and
`public/artifacts/current/server_endpoints.json`, then prints the pinned baseline,
published artifacts, and whether key local API routes such as `POST /prompt`,
`GET /queue`, `GET /history/{prompt_id}`, and `GET /ws` are present.

## What This Repository Is

ComfyUI StarChart is a version-pinned, source-extracted companion reference for
ComfyUI developers. It publishes:

- a self-hostable Astro Starlight documentation site
- extracted JSON artifacts for selected ComfyUI API, hook, and schema surfaces
- repo-local maintainer tooling for refresh, verification, and publication

This repository is not the official ComfyUI documentation. Use
[docs.comfy.org](https://docs.comfy.org/) for authoritative official guidance.

## Background

I created ComfyUI StarChart because ComfyUI has a real developer-documentation
gap.

There is plenty of ComfyUI content on the internet, but much of it is hard to
trust as a development baseline. Reddit threads can be helpful but scattered.
YouTube videos can show a workflow but often age badly. Community repos may
solve one narrow problem, then stop updating. Even the official docs, while
important, are not trying to be a version-pinned, machine-readable developer
reference for every tooling and contribution task.

That leaves developers in a frustrating spot: if you want to contribute to
ComfyUI, build against it, or verify how a surface changed, you often end up
manually diffing source, chasing outdated examples, and reconstructing context
from multiple places.

StarChart is my attempt to make that workflow less fragile.

The core idea is simple: pin upstream versions, snapshot the relevant source,
extract structured artifacts from those snapshots, and publish docs that stay
tied to evidence instead of memory. That makes it easier to answer questions
like:

- Is there a new hook?
- What changed about that hook?
- What is different in the pinned core compared with the previous baseline?
- Which route, schema field, or extension surface actually changed?
- Where should a developer start for custom nodes, extensions, integrations, or runtime metrics work?

I also built this with agents in mind.

One of my recurring frustrations was that I like using agents, but there was no
single resource I trusted to give them precise, bounded, evidence-backed ComfyUI
development context. Most web material is written for humans to skim, not for an
agent to query conservatively. Agents do better when the surface is structured,
stable, and explicit about what is guaranteed versus best-effort.

ComfyUI StarChart gives them that surface:

- canonical JSON artifacts for pinned API, hook, and schema data
- a merged support index for docs routing and tooling-task discovery
- stable published paths and checksums via `manifest.json`
- start-here docs for task routing

In practice, that means an agent can more reliably answer questions such as:

- how do I create a custom node against this pinned baseline?
- where should I look to build an extension?
- what changed between two known versions?
- which doc page is the right next read for metrics capture, route work, or schema validation?

The long-term goal is bigger than a readable docs site. I want StarChart to be a
useful working substrate for both humans and agents: something you can inspect,
diff, route through, and build on without depending on vague memory or unstable
community breadcrumbs.

## Who This Repo Is For

- **Consumers** building custom nodes, extensions, integrations, or tools
- **Agents** using the tooling schema, merged support index, and JSON artifacts to route, inspect, and interact with the repo's published developer surface
- **Contributors** editing docs, examples, or other hand-authored content
- **Maintainers** running verifiers, refreshes, artifact publication, or CI/workflow changes

Start here:

- **Consumers:** [Docs home](src/content/docs/index.md)
  - [Artifact Consumer](src/content/docs/start-here/artifact-consumer.md)
  - [Tooling Builder](src/content/docs/start-here/tooling-builder.md)
  - [Local API Integration](src/content/docs/start-here/service-integration.md)
  - [Extension Developer](src/content/docs/start-here/extension-developer.md)
  - [Custom Node Author](src/content/docs/start-here/author.md)
- **Agents:** start with [Docs home](src/content/docs/index.md), then use [Tooling Builder](src/content/docs/start-here/tooling-builder.md), [Machine-Readable Artifacts](src/content/docs/reference/machine-readable-artifacts.md), and [AGENTS.md](AGENTS.md)
- **Contributors:** [CONTRIBUTING.md](CONTRIBUTING.md) plus the editorial policy stack under `src/content/docs/reference/`
- **Maintainers:** [CONTRIBUTING.md](CONTRIBUTING.md) for canonical workflows, plus [AGENTS.md](AGENTS.md) for startup-critical repo guidance

## Maintainer Quick Start

Supported Python: `3.11+`
Supported Node.js for site/framework work: `24.x`

**Windows bootstrap:**

```bash
py -3.11 -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS bootstrap:**

```bash
python -m venv .venv
source .venv/bin/activate
```

**After activation (all platforms):**

```bash
python -m pip install --require-hashes -r requirements.lock
python -m pip install -e .
npm ci
python -m unittest discover -s tests -v
npm run build
```

Serve locally with `npm run dev`.

After the first bootstrap, use the activated venv for all subsequent commands:

```bash
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # Linux / macOS
```

Maintainer notes:

- `.python-version` contains `3.11` for toolchains that auto-select Python
- install from `requirements.lock`
- edit direct Python dependencies in `requirements.in`
- use `python scripts/verify/run_all.py` as the default maintainer-grade local gate
- once the venv is active, `python` resolves to the venv interpreter and version is always `3.11.x`

## Machine-Readable Artifacts

Canonical extracted artifacts are published from pinned upstream snapshots:

- `artifacts/current/server_endpoints.json`
- `artifacts/current/js_hooks.json`
- `artifacts/current/node_api_schema.json`
- `artifacts/current/websocket_events.json`
- `artifacts/manifest.json` for canonical artifact discovery and checksums

Support artifacts are also published for bounded routing and change analysis:

- `artifacts/docs-index.json`
- `artifacts/delta-summary.json`
- `artifacts/refresh-provenance.json`

For artifact URLs, contract tiers, schemas, and consumer guidance, see
[Machine-Readable Artifacts](src/content/docs/reference/machine-readable-artifacts.md).

Consumer starter examples live in
[src/content/docs/start-here/artifact-consumer.md](src/content/docs/start-here/artifact-consumer.md)
and `examples/consumers/`.

## Example Validation

Repo-local examples are not accepted as correct because they read well. Their
evidence is tracked in `references/example-validation-matrix.json` and checked by
examples-only verifiers:

```bash
python scripts/verify/example_surface_integrity.py
python scripts/verify/example_validation_matrix.py
python scripts/verify/shell_examples_syntax.py
```

Live ComfyUI validation is opt-in because it depends on a running runtime and an
installed checkpoint. For a local runtime such as `D:/projects/comfyui-test-runtime`,
run:

```bash
python scripts/verify/example_runtime_smoke.py --url http://127.0.0.1:8188 --comfyui-root D:/projects/comfyui-test-runtime --model-name <installed-checkpoint.safetensors>
```

Use `--skip-prompt` when you only want object-info, WebSocket, custom-node, or
extension-route checks.

## Maintainer Workflow Routing

- [CONTRIBUTING.md](CONTRIBUTING.md) is the canonical maintainer workflow guide
- [AGENTS.md](AGENTS.md) is the startup-oriented quick reference for repo constraints, commands, and task routing
- `python scripts/verify/run_all.py` is the default blocking local verification wrapper

Use `CONTRIBUTING.md` for workflow inventory, lockfile regeneration,
extractor/generator workflows, snapshot refreshes, runtime capture, and the
full verification matrix.

## Scope Boundaries

StarChart intentionally does not try to be:

- an official docs replacement
- a community wiki
- a package registry
- an unbounded maintainer handbook inside the published docs tree

See CONTRIBUTING.md Non-Goal Addendum for the full list of rejected feature classes and their rationale.

## Project Health Files

- [SECURITY.md](SECURITY.md) -- private vulnerability reporting guidance
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) -- participation expectations for public collaboration
