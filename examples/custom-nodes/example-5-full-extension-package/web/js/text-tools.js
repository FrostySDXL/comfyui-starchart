// Frontend extension for the example-5 full extension package.
// Uses official extension hooks to apply a visible editor accent to nodes in
// the "example/text" category.

import { app } from "../../scripts/app.js";

const TARGET_CATEGORY = "example/text";

function isExampleTextNode(nodeOrData) {
  return typeof nodeOrData?.category === "string" && nodeOrData.category.startsWith(TARGET_CATEGORY);
}

function applyTextNodeAccent(node) {
  if (!node || node.__exampleTextToolsApplied) {
    return;
  }

  node.__exampleTextToolsApplied = true;
  node.color = "#355a7a";
  node.bgcolor = "#223447";
  node.setDirtyCanvas?.(true, true);
}

app.registerExtension({
  name: "example.texttools",

  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (!isExampleTextNode(nodeData)) {
      return;
    }

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const result = onNodeCreated?.apply(this, arguments);
      applyTextNodeAccent(this);
      return result;
    };
  },

  nodeCreated(node) {
    if (isExampleTextNode(node)) {
      applyTextNodeAccent(node);
    }
  },
});
