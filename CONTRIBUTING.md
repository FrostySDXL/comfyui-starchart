# Contributing

## Setup

```bash
python -m pip install -r requirements.txt
```

## Repo Conventions

- Keep Phase 1 pages as scaffolds unless you are intentionally replacing placeholders with researched content.
- Update both human docs and machine-readable references when behavior changes.
- Prefer small, verifiable changes.
- Do not add emojis or emoticons to docs.

## Verification Commands

Run the narrowest relevant checks first, then broader checks before completion:

```bash
python -m unittest discover -s tests
mkdocs build
```

If you change extraction or generation scripts, include the exact command and output in your handoff or PR notes.

## Documentation Rules

- Every content page should keep explicit primary sources.
- Replace placeholder text only when backed by source material.
- Keep generated artifacts aligned with their source JSON.
