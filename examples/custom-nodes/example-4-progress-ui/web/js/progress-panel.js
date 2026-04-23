// Frontend extension that listens for the custom "my-progress" event
// emitted by ProgressEmitterNode and renders a visible progress indicator.
//
// IMPORTANT: "my-progress" is an EXAMPLE custom event name used by the
// example-4-progress-ui package. It is NOT an official ComfyUI event.
// Official ComfyUI events are defined in the ComfyUI server and documented
// at docs.comfy.org. Custom event names will not be recognized by ComfyUI
// unless a frontend extension is present that registers a listener for them.
//
// This pattern only works in the ComfyUI editor (not in API mode), because
// it requires the frontend extension system to be running.

import { app } from "../../scripts/app.js";

app.registerExtension({
  name: "example.progress",

  setup() {
    const panels = new Map();

    function panelOrder() {
      return Array.from(panels.keys());
    }

    function layoutPanels() {
      const ids = panelOrder();
      ids.forEach((id, index) => {
        const panel = panels.get(id);
        if (!panel) {
          return;
        }
        panel.style.bottom = `${20 + index * 110}px`;
      });
    }

    function getPanel(nodeId) {
      let panel = panels.get(nodeId);
      if (panel) {
        return panel;
      }

      panel = document.createElement("div");
      panel.style.cssText = `
        position: fixed;
        right: 20px;
        background: rgba(30, 30, 50, 0.92);
        color: #e0e0ff;
        padding: 12px 16px;
        border-radius: 8px;
        font-family: sans-serif;
        font-size: 13px;
        z-index: 1000;
        min-width: 220px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
      `;
      document.body.appendChild(panel);
      panels.set(nodeId, panel);
      layoutPanels();
      return panel;
    }

    function messageHandler(event) {
      const { node_id: nodeId = "unknown", progress, stage } = event.detail || {};
      const panel = getPanel(nodeId);

      // Clear previous content and rebuild with DOM calls to avoid
      // innerHTML with payload-derived strings (copy-paste safety).
      panel.innerHTML = "";
      const percent = Math.round((progress || 0) * 100);

      const titleDiv = document.createElement("div");
      titleDiv.style.cssText = "margin-bottom: 6px; font-weight: 600;";
      titleDiv.textContent = `Node ${nodeId}`;

      const barOuter = document.createElement("div");
      barOuter.style.cssText = "background: rgba(255,255,255,0.15); border-radius: 4px; height: 8px; overflow: hidden;";
      const barInner = document.createElement("div");
      barInner.style.cssText = `width: ${percent}%; height: 100%; background: #7b8fff; transition: width 0.2s ease;`;
      barOuter.appendChild(barInner);

      const stageDiv = document.createElement("div");
      stageDiv.style.cssText = "margin-top: 6px; font-size: 12px; opacity: 0.85;";
      stageDiv.textContent = stage || "";

      const pctDiv = document.createElement("div");
      pctDiv.style.cssText = "margin-top: 2px; font-size: 11px; opacity: 0.6;";
      pctDiv.textContent = `${percent}%`;

      panel.appendChild(titleDiv);
      panel.appendChild(barOuter);
      panel.appendChild(stageDiv);
      panel.appendChild(pctDiv);

      // Remove the panel when progress reaches 100%
      if (progress >= 1.0) {
        setTimeout(() => {
          if (panels.has(nodeId)) {
            panel.remove();
            panels.delete(nodeId);
            layoutPanels();
          }
        }, 1500);
      }
    }

    // Register the listener for our custom event name.
    // This will not conflict with official ComfyUI events because it uses
    // a namespaced custom event name.
    app.api.addEventListener("my-progress", messageHandler);
  },
});
