import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const [, , baseUrlArg, audienceFilter = "consumer"] = process.argv;

if (!baseUrlArg) {
  console.error(
    "Usage: node load_docs_index.mjs <site-base-url> [audience-filter]",
  );
  process.exit(1);
}

const docsIndexUrl = new URL("artifacts/docs-index.json", ensureTrailingSlash(baseUrlArg));
const docsIndex = await loadJson(docsIndexUrl);

const pages = (docsIndex.pages || []).filter((page) => {
  if (!audienceFilter) {
    return true;
  }

  return page.audience === audienceFilter || page.nav_section?.includes("Start Here");
});

console.log(JSON.stringify({
  artifact: docsIndex.artifact,
  docs_index_is_optional: true,
  audience_filter: audienceFilter,
  matches: pages.slice(0, 5).map((page) => ({
    title: page.title,
    path: page.path,
    nav_section: page.nav_section,
    evidence: page.evidence,
  })),
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
