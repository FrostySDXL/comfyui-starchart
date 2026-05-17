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

## Conventions

- Every subdirectory has its own `README.md` with evidence labels and scope statements.
- Shell scripts (`.sh` files) are validated by `python scripts/verify/shell_examples_syntax.py`.
- Examples are hand-authored pattern illustrations, not extracted references.
- New examples should follow the structure of the nearest existing family.

## Adding an example

1. Place files in the matching family directory.
2. Add or update that directory's `README.md` to list the new example.
3. Run `python scripts/verify/example_surface_integrity.py` to confirm the
   example surface is complete.
