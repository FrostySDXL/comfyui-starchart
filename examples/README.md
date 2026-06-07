# Examples

**Evidence:** Operational guidance (this README); see each subdirectory for
content-level evidence labels.

## Example families

| Directory | Purpose |
|-----------|---------|
| `api-calls/` | Raw API call patterns (POST /prompt payloads, curl examples, shell scripts) |
| `consumers/` | Tooling-consumer starters that load published artifacts in Python, JavaScript, shell/jq, and combined live-API patterns |
| `custom-nodes/` | Custom node authoring examples from minimal template through full extension package |
| `extensions/` | Extension architecture patterns (server hooks, frontend hooks) |
| `workflows/` | Workflow JSON examples with parameter-injection commentary |

## High-value starter examples

- `workflows/api-execution-tracking-workflow.json` - repo-authored workflow
  fixture for prompt-submission and execution-tracking walkthroughs
- `extensions/minimal-route-registration/` - smallest route-registration pattern
  that isolates `PromptServer.instance.routes` usage
- `consumers/python-artifact-delta-reader/` - Python starter for reading
  `artifacts/delta-summary.json` without treating it as a canonical manifest
  artifact

## Conventions

- Every subdirectory has its own `README.md` with evidence labels and scope statements.
- Every example directory with a `README.md` must have a matching entry in
  `references/example-validation-matrix.json`.
- Shell scripts (`.sh` files) are validated by `python scripts/verify/shell_examples_syntax.py`.
- Examples are hand-authored pattern illustrations, not extracted references.
- New examples should follow the structure of the nearest existing family.
- Be explicit about whether an example is source-backed, repo-authored, or a
  starter scaffold.

## Validation tiers

Examples are validated by evidence tier, not by self-claim:

- `static` - repo-local parse/path/README checks
- `offline_unit` - unit tests or mocked/local fixture tests
- `pinned_source` - claims tied to retained snapshots or docs.comfy.org
- `runtime_smoke` - opt-in live ComfyUI validation using
  `scripts/verify/example_runtime_smoke.py`
- `pattern_only_caveated` - illustrative pattern that needs live validation
  before relying on runtime behavior

Use `references/example-validation-matrix.json` for the current per-example
evidence record.

## Adding an example

1. Place files in the matching family directory.
2. Add or update that directory's `README.md` to list the new example.
3. Add or update the entry in `references/example-validation-matrix.json`.
4. Run `python scripts/verify/example_surface_integrity.py` to confirm the
   example surface is complete.
5. Run `python scripts/verify/example_validation_matrix.py` to confirm evidence
   tiers are explicit.
6. If claiming runtime validation, run `python scripts/verify/example_runtime_smoke.py`
   against a live ComfyUI instance and record the exact command and result.
