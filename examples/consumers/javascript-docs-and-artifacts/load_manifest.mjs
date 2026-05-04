import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const [, , baseUrlArg, artifactKey = "server_endpoints.json"] = process.argv;

if (!baseUrlArg) {
  console.error(
    "Usage: node load_manifest.mjs <site-base-url> [artifact-key]",
  );
  process.exit(1);
}

const manifestUrl = new URL("artifacts/manifest.json", ensureTrailingSlash(baseUrlArg));
const manifest = await loadJson(manifestUrl);
const entry = manifest.artifacts?.[artifactKey];

if (!entry) {
  console.error(`Unknown artifact key: ${artifactKey}`);
  process.exit(1);
}

console.log(JSON.stringify({
  artifact_schema_version: manifest.artifact_schema_version,
  artifact_key: artifactKey,
  current_url: entry.current_url,
  versioned_url: entry.versioned_url,
  schema_url: manifest.schemas?.[artifactKey]?.schema_url ?? null,
  support_artifact_note: "Use docs-index.json only for docs routing, not canonical artifact discovery.",
}, null, 2));

async function loadJson(url) {
  if (url.protocol === "file:") {
    return JSON.parse(await readFile(fileURLToPath(url), "utf8"));
  }

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load ${url}: ${response.status}`);
  }

  return response.json();
}

function ensureTrailingSlash(value) {
  return value.endsWith("/") ? value : `${value}/`;
}
