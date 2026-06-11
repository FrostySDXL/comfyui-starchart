import siteConfig from './site-config.json' with { type: 'json' };

const LEADING_SKIPPABLE_NODE_TYPES = new Set(['html', 'definition']);

export function normalizeSiteBaseNoTrailingSlash(site, base) {
  const normalized = `${String(site || '').replace(/\/+$/u, '')}/${String(base || '')
    .replace(/^\/+|\/+$/gu, '')
    .replace(/^\/+/, '')}`;
  return normalized.replace(/\/+$/u, '') || '';
}

function normalizeBasePath(base) {
  const normalized = `/${String(base || '').replace(/^\/+|\/+$/gu, '')}`;
  return normalized.replace(/\/+$/u, '') || '';
}

const SITE_BASE = normalizeBasePath(siteConfig.base);

function splitUrlParts(url) {
  const hashIndex = url.indexOf('#');
  const queryIndex = url.indexOf('?');

  let pathEnd = url.length;
  if (hashIndex !== -1) pathEnd = Math.min(pathEnd, hashIndex);
  if (queryIndex !== -1) pathEnd = Math.min(pathEnd, queryIndex);

  return {
    path: url.slice(0, pathEnd),
    suffix: url.slice(pathEnd),
  };
}

/**
 * Normalize path segments by resolving `.` and `..` components.
 * @param {string[]} segments - Array of path segments
 * @returns {string[]} - Normalized segments
 */
function normalizeSegments(segments) {
  const result = [];
  for (const seg of segments) {
    if (seg === '..') {
      result.pop();
    } else if (seg !== '.' && seg !== '') {
      result.push(seg);
    }
  }
  return result;
}

/**
 * Rewrite a markdown link href to a Starlight-compatible route.
 * When currentFilePath is provided, resolves relative links to absolute URL paths.
 * @param {string} url - The original href value
 * @param {string} [currentFilePath] - Path of the current markdown file relative to content root
 * @returns {string} - Rewritten href
 */
export function rewriteDocLinkHref(url, currentFilePath) {
  if (typeof url !== 'string' || !url) return url;
  if (/^(?:[a-z]+:|\/\/|#)/i.test(url)) return url;

  const { path, suffix } = splitUrlParts(url);
  if (!path.endsWith('.md')) return url;

  const normalizedPath = path.replaceAll('\\', '/');

  // Convert markdown path to route path
  let routePath;
  if (normalizedPath === 'index.md') {
    routePath = '';
  } else if (normalizedPath.endsWith('/index.md')) {
    routePath = normalizedPath.slice(0, -'index.md'.length);
  } else {
    routePath = `${normalizedPath.slice(0, -'.md'.length)}/`;
  }

  // If we have the current file path and the link is relative, resolve to absolute
  if (currentFilePath && !routePath.startsWith('/')) {
    const currentNormalized = currentFilePath.replaceAll('\\', '/');
    // Get directory of current file (remove filename)
    const currentDir = currentNormalized.includes('/')
      ? currentNormalized.slice(0, currentNormalized.lastIndexOf('/'))
      : '';

    // Combine current directory with relative route path and normalize
    const combined = currentDir ? `${currentDir}/${routePath}` : routePath;
    const segments = combined.split('/');
    const normalized = normalizeSegments(segments);

    // Return absolute path with site base
    const normalizedRoute = normalized.join('/');
    routePath = normalizedRoute ? `${SITE_BASE}/${normalizedRoute}/` : `${SITE_BASE}/`;
    // Clean up double slashes
    routePath = routePath.replace(/\/+/g, '/');
  }

  return `${routePath}${suffix}`;
}

function visitNodes(node, callback) {
  if (!node || typeof node !== 'object') return;
  callback(node);
  if (Array.isArray(node.children)) {
    for (const child of node.children) {
      visitNodes(child, callback);
    }
  }
}

export function remarkRewriteDocLinks() {
  return (tree, file) => {
    // Get the current file's path relative to content root
    // Astro provides this via file.path or file.history[0]
    const rawPath = file?.path || file?.history?.[0] || null;

    // Extract the path relative to src/content/docs/
    let currentFilePath = null;
    if (rawPath) {
      const normalized = rawPath.replaceAll('\\', '/');
      const docsMarker = 'src/content/docs/';
      const markerIndex = normalized.indexOf(docsMarker);
      if (markerIndex !== -1) {
        currentFilePath = normalized.slice(markerIndex + docsMarker.length);
      }
    }

    visitNodes(tree, (node) => {
      if ((node.type === 'link' || node.type === 'definition') && typeof node.url === 'string') {
        node.url = rewriteDocLinkHref(node.url, currentFilePath);
      }
    });
  };
}

export function stripLeadingH1(tree) {
  if (!Array.isArray(tree?.children)) return;

  let headingIndex = -1;
  for (let index = 0; index < tree.children.length; index += 1) {
    const node = tree.children[index];
    if (LEADING_SKIPPABLE_NODE_TYPES.has(node?.type)) {
      continue;
    }
    if (node?.type === 'heading' && node.depth === 1) {
      headingIndex = index;
    }
    break;
  }

  if (headingIndex !== -1) {
    tree.children.splice(headingIndex, 1);
  }
}

export function remarkStripLeadingH1() {
  return (tree) => {
    stripLeadingH1(tree);
  };
}
