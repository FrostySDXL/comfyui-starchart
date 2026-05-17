const LEADING_SKIPPABLE_NODE_TYPES = new Set(['html', 'definition']);

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

export function rewriteDocLinkHref(url) {
  if (typeof url !== 'string' || !url) return url;
  if (/^(?:[a-z]+:|\/\/|#)/i.test(url)) return url;

  const { path, suffix } = splitUrlParts(url);
  if (!path.endsWith('.md')) return url;

  const normalizedPath = path.replaceAll('\\', '/');
  let routePath;
  if (normalizedPath === 'index.md') {
    routePath = '';
  } else if (normalizedPath.endsWith('/index.md')) {
    routePath = normalizedPath.slice(0, -'index.md'.length);
  } else {
    routePath = `${normalizedPath.slice(0, -'.md'.length)}/`;
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
  return (tree) => {
    visitNodes(tree, (node) => {
      if ((node.type === 'link' || node.type === 'definition') && typeof node.url === 'string') {
        node.url = rewriteDocLinkHref(node.url);
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
