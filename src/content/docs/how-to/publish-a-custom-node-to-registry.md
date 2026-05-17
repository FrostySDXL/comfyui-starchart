---
title: "Publish a Custom Node to the Registry"
---

**Evidence:** Official docs-backed from docs.comfy.org
**Last Updated:** 2026-05-13
**Primary Source:** https://docs.comfy.org/registry/publishing

## Primary Sources

- https://docs.comfy.org/registry/publishing
- https://docs.comfy.org/registry/specifications
- https://docs.comfy.org/registry/cicd

## Scope

Use this page when you are ready to publish a custom node through the ComfyUI
registry flow that powers Manager discovery.

This page covers publication readiness and the supported publish steps. It does
not replace end-user installation guidance.

## 1. Create the publisher identity and API key first

1. Go to the Comfy Registry and create a publisher.
2. Record the publisher ID shown on your profile.
3. Create a registry publishing API key for that publisher.
4. Store the API key safely. The official docs note that if you lose it, you
   must create a new one.

Before state: no publisher identity and no publishing token.
After state: you have the publisher ID and a publishing API key ready for CLI or
CI use.

## 2. Add the registry metadata to `pyproject.toml`

1. Initialize the node metadata with:

   ```bash
   comfy node init
   ```

2. Confirm the generated `pyproject.toml` includes the required project fields,
   including:

   - `[project].name`
   - `[project].version`
   - `[project].description`
   - `[project.urls].Repository`
   - `[tool.comfy].PublisherId`

3. Add recommended compatibility metadata when it applies, such as:

   - `requires-python`
   - `classifiers`
   - `comfyui-frontend-package` dependency constraints for frontend-version
     compatibility
   - `[tool.comfy].requires-comfyui`

4. Use the registry specification rules for naming, semantic versioning, and
   metadata shape instead of inventing your own contract.

Before state: repo exists, but registry metadata is incomplete.
After state: repo metadata matches the official registry publishing contract.

## 3. Publish with the CLI when you want a manual release

1. Run:

   ```bash
   comfy node publish
   ```

2. Enter the publisher API key when prompted.
3. Wait for the publish result and registry URL.
4. Treat the returned registry URL as the confirmation that the version was
   published.

The official docs also warn that Windows paste behavior can append an extra
character to the hidden API key field. If the paste fails unexpectedly, retry
carefully instead of assuming the registry is broken.

## 4. Add GitHub Actions when you want a CI-driven publish path

1. Create a repository secret named `REGISTRY_ACCESS_TOKEN`.
2. Store your publisher API key in that secret.
3. Add the documented publish workflow so pushes that change `pyproject.toml`
   can trigger publication.
4. If your default branch is not `main`, adjust the workflow branch filter.
5. Test the workflow by pushing a version bump in `pyproject.toml`.

The registry CI/CD docs also point to Comfy Action when you want workflow-based
test runs before publication.

## 5. Keep publication readiness separate from user installation

1. Publishing makes the node available to the registry-backed ecosystem.
2. Publishing does not replace install verification for end users.
3. If you need to explain how users install or update the node after release,
   link them to the install and Manager workflow pages instead of duplicating
   those instructions here.

## What to expect when it works

- your repository has the metadata the registry expects
- a publisher identity and API key are in place
- `comfy node publish` or the GitHub Action produces a published registry entry
- you can describe the node as registry-published without implying that user
  installation details are handled on this page

## Read Next

- [Integrate with Manager](integrate-with-manager.md)
- [Install Custom Nodes Safely](install-custom-nodes-safely.md)
- [Enable and Use Manager on Manual or Portable Installs](enable-and-use-manager-on-manual-or-portable-installs.md)
