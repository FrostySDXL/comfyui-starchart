import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

function createPanel() {
  const panel = document.createElement("div");
  panel.style.cssText = [
    "position: fixed",
    "top: 20px",
    "right: 20px",
    "width: 320px",
    "padding: 12px",
    "border-radius: 10px",
    "background: rgba(22, 24, 34, 0.96)",
    "color: #e7ebff",
    "font: 12px/1.4 sans-serif",
    "box-shadow: 0 8px 20px rgba(0, 0, 0, 0.35)",
    "z-index: 1000",
  ].join(";");

  const title = document.createElement("div");
  title.textContent = "Benchmark Harness";
  title.style.cssText = "font-size: 13px; font-weight: 700; margin-bottom: 8px;";

  const button = document.createElement("button");
  button.type = "button";
  button.textContent = "Refresh stats";
  button.style.cssText = [
    "margin-bottom: 8px",
    "padding: 6px 10px",
    "border: 0",
    "border-radius: 6px",
    "background: #7587ff",
    "color: #fff",
    "cursor: pointer",
  ].join(";");

  const status = document.createElement("div");
  status.style.cssText = "opacity: 0.85; margin-bottom: 8px;";

  const output = document.createElement("pre");
  output.style.cssText = [
    "margin: 0",
    "white-space: pre-wrap",
    "word-break: break-word",
    "max-height: 280px",
    "overflow: auto",
    "padding: 8px",
    "border-radius: 6px",
    "background: rgba(255, 255, 255, 0.06)",
  ].join(";");

  panel.append(title, button, status, output);
  document.body.appendChild(panel);
  return { button, status, output };
}

function formatMetrics(data) {
  const lines = [];
  lines.push(`latest_prompt_id: ${data.latest_prompt_id ?? "none"}`);
  lines.push(`active_node_count: ${data.active_node_count}`);
  lines.push("");

  if (!data.node_metrics?.length) {
    lines.push("No node timings recorded yet.");
    return lines.join("\n");
  }

  for (const metric of data.node_metrics) {
    const label = metric.class_type ? `${metric.node_id} (${metric.class_type})` : metric.node_id;
    lines.push(`${label}`);
    lines.push(`  runs: ${metric.runs}`);
    lines.push(`  last_duration_ms: ${metric.last_duration_ms ?? "n/a"}`);
    lines.push(`  average_duration_ms: ${metric.average_duration_ms ?? "n/a"}`);
    lines.push(`  finish_without_start: ${metric.finish_without_start}`);
  }

  return lines.join("\n");
}

app.registerExtension({
  name: "example.benchmarkHarness",

  setup() {
    const panel = createPanel();

    async function refresh() {
      try {
        const response = await api.fetchApi("/benchmark-harness/stats");
        const data = await response.json();
        panel.status.textContent = `hook: ${data.hook_status.detail}`;
        panel.output.textContent = formatMetrics(data);
      } catch (error) {
        panel.status.textContent = "hook: request failed";
        panel.output.textContent = String(error);
      }
    }

    panel.button.addEventListener("click", refresh);

    for (const eventName of ["executing", "executed", "execution_success", "execution_error"]) {
      api.addEventListener(eventName, refresh);
    }

    refresh();
  },
});
