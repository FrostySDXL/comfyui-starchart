# Example 5: Full Extension Package Layout

**Status:** Pattern example
**Level:** Advanced -- builds on examples 1 through 4

## What This Example Is

A complete example package that demonstrates the full
structure of a ComfyUI custom node pack. Includes multiple backend nodes,
a frontend JavaScript extension, dependency management, lifecycle scripts,
and Manager-aware packaging conventions.

This is the final step in the example ladder. After working through
examples 1-4, this package shows how to assemble all the pieces into a
package layout that is suitable for publication work or standalone
distribution.

## Files

```
example-5-full-extension-package/
  __init__.py              -- package entry point (NODE_CLASS_MAPPINGS, etc.)
  requirements.txt         -- Python dependencies
  install.py               -- lifecycle: runs after first install
  enable.py                -- lifecycle: runs when the package is re-enabled
  disable.py               -- lifecycle: runs when the package is disabled
  uninstall.py             -- lifecycle: runs before removal
  nodes/
    text_processor_node.py -- V1 node: text transformation
    text_metadata_node.py -- V1 node: pipeline metadata / utility
  web/js/
    text-tools.js          -- frontend extension: supported hook-based accent for text nodes
  README.md                -- this file
```

## What to Study

- How to structure a package with multiple node files under a `nodes/` directory
- How `__init__.py` aggregates `NODE_CLASS_MAPPINGS` from multiple node files
- How `WEB_DIRECTORY` points the frontend extension loader to the JS directory
- How lifecycle scripts (`install.py`, `enable.py`, `disable.py`, `uninstall.py`)
  form a contract with ComfyUI-Manager
- How `requirements.txt` declares Python dependencies
- How a frontend extension enhances the editor for your nodes

## Package Entry Point

`__init__.py` aggregates all node classes and exposes the package-facing
interface:

```python
from .nodes import (
    NODE_CLASS_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS,
)

WEB_DIRECTORY = "./web/js"

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
```

Each node file under `nodes/` uses standard V1 registration:

```python
NODE_CLASS_MAPPINGS = {"Text Processor": TextProcessorNode}
NODE_DISPLAY_NAME_MAPPINGS = {"Text Processor": "Text Processor"}
```

## Lifecycle Scripts

Lifecycle scripts are optional but improve the user experience when your
package is managed by ComfyUI-Manager.

### install.py

Runs after the package is first cloned into `custom_nodes/`. Use it to:

- install Python dependencies from `requirements.txt`
- download external assets or models
- run one-time setup tasks

```python
# install.py -- zero-dependency example pattern
def install():
    return None
```

### enable.py

Runs when the package is re-enabled after being disabled. Use it to:

- restore any state that was cleaned up in `disable.py`
- re-register resources

```python
# enable.py -- example pattern
def enable():
    pass  # restore state, re-register
```

### disable.py

Runs when the package is disabled (Manager appends `.disabled` to the folder
name). Use it to:

- save state that should persist across disable/enable cycles
- release resources

```python
# disable.py -- example pattern
def disable():
    pass  # save state, release resources
```

### uninstall.py

Runs before the package directory is removed. Use it to:

- clean up assets created by the package
- remove installed dependencies (use with caution)

```python
# uninstall.py -- example pattern
def uninstall():
    pass  # remove assets, dependencies
```

**Note:** `uninstall.py` is not guaranteed to run. Users may delete the
directory manually or use Manager's uninstall without running the script.
Do not put critical cleanup logic here as the only path.

## requirements.txt

Declare minimal Python dependencies. Keep versions loose to reduce conflicts:

```
# requirements.txt -- zero-dependency example
# Add packages here only when your nodes actually import them.
```

Do not pin exact versions unless a specific version is required for
compatibility. Avoid adding ComfyUI itself as a dependency.

**Note:** The text-node nodes in this example (`text_processor_node.py`,
`text_metadata_node.py`) do not require any external Python packages, so this
example ships as zero-dependency.

## Frontend Extension

`web/js/text-tools.js` demonstrates a minimal frontend extension that:

- registers an extension name (`example.texttools`)
- uses `beforeRegisterNodeDef` to patch node-type creation behavior
- uses `nodeCreated` as a second safety net for loaded or newly created nodes
- applies a visible editor accent to nodes in the `example/text` category

```javascript
app.registerExtension({
  name: "example.texttools",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.category?.startsWith("example/text")) {
      const onNodeCreated = nodeType.prototype.onNodeCreated;
      nodeType.prototype.onNodeCreated = function () {
        const result = onNodeCreated?.apply(this, arguments);
        this.color = "#355a7a";
        this.bgcolor = "#223447";
        return result;
      };
    }
  },
  nodeCreated(node) {
    if (node.category?.startsWith("example/text")) {
      node.color = "#355a7a";
      node.bgcolor = "#223447";
    }
  },
});
```

This keeps the example on supported frontend patterns documented elsewhere in
the repo. It does not depend on custom DOM overlays or undocumented node-DOM
attachment behavior.

## Manager and Registry Era Expectations

### What is officially supported by Manager

The official ComfyUI-Manager publication flow expects:

- a git repository (typically GitHub)
- registration via `custom-node-list.json` (legacy) or the registry
  (registry.comfy.org, current preferred path)
- `requirements.txt` for Python dependencies
- optional lifecycle scripts (`install.py`, `enable.py`, `disable.py`,
  `uninstall.py`)

### Legacy vs registry-backed flow

- **Legacy flow**: submit a PR to ComfyUI-Manager adding your repo to
  `custom-node-list.json`. Users can install via git URL or the Manager UI.
- **Registry-backed flow**: register your package with registry.comfy.org.
  The new Manager UI installs from the registry, not arbitrary git URLs.
  This is more secure and reliable.

This example demonstrates the package structure commonly used with both flows.
Manager or registry availability still depends on the separate listing or
publication step for the chosen channel.

The `node_list.json` file is only needed if your package does not follow
the standard `NODE_CLASS_MAPPINGS` / `NODE_DISPLAY_NAME_MAPPINGS` pattern.

## Evidence Level

- Package structure: community pattern based on ComfyUI-Manager conventions
- Lifecycle scripts: documented in official ComfyUI-Manager docs
- Registry vs legacy flow: Manager conventions documented at docs.comfy.org; registry
  operation documented at registry.comfy.org
- This example: hand-authored to illustrate established conventions
