import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

/** @typedef {{ label?: string, path?: string, items?: SidebarEntry[] }} SidebarEntry */

export const SIDEBAR_DATA_PATH = fileURLToPath(new URL('./sidebar-data.json', import.meta.url));

/** @returns {SidebarEntry[]} */
export function loadSidebarData() {
  return JSON.parse(readFileSync(SIDEBAR_DATA_PATH, 'utf8'));
}

/** @param {string} docPath */
export function docPathToSlug(docPath) {
  const normalizedPath = docPath.replaceAll('\\', '/');
  if (!normalizedPath.endsWith('.md')) {
    throw new Error(`Sidebar page path must end in .md: ${docPath}`);
  }

  const markdownStem = normalizedPath.slice(0, -3);
  if (markdownStem === 'index') {
    return '';
  }

  if (markdownStem.endsWith('/index')) {
    return markdownStem.slice(0, -'/index'.length);
  }

  return markdownStem;
}

/** @param {string} docPath */
function fallbackLabelFromPath(docPath) {
  const normalizedPath = docPath.replaceAll('\\', '/');
  const leaf = normalizedPath.split('/').pop()?.replace(/\.md$/, '') ?? normalizedPath;
  return leaf
    .split('-')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

/**
 * @param {SidebarEntry[]} entries
 * @returns {any[]}
 */
export function toStarlightSidebar(entries) {
  return entries.map((entry) => {
    if (Array.isArray(entry?.items)) {
      return {
        label: entry.label,
        items: toStarlightSidebar(entry.items),
      };
    }

    if (typeof entry?.path === 'string') {
      return {
        label: entry.label ?? fallbackLabelFromPath(entry.path),
        slug: docPathToSlug(entry.path),
      };
    }

    throw new Error(`Invalid sidebar entry: ${JSON.stringify(entry)}`);
  });
}
