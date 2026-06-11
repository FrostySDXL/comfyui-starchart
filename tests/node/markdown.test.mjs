import test from 'node:test';
import assert from 'node:assert/strict';

import {
  normalizeSiteBaseNoTrailingSlash,
  rewriteDocLinkHref,
  stripLeadingH1,
} from '../../src/site/markdown.js';

test('normalizeSiteBaseNoTrailingSlash matches Python formula for subpath with trailing slash', () => {
  assert.equal(
    normalizeSiteBaseNoTrailingSlash('https://example.com', '/docs/'),
    'https://example.com/docs',
  );
});

test('rewriteDocLinkHref rewrites markdown page links to Starlight-style routes', () => {
  assert.equal(rewriteDocLinkHref('reference/machine-readable-artifacts.md'), 'reference/machine-readable-artifacts/');
  assert.equal(rewriteDocLinkHref('../api/endpoints.md'), '../api/endpoints/');
  assert.equal(rewriteDocLinkHref('tutorials/index.md'), 'tutorials/');
  assert.equal(rewriteDocLinkHref('../index.md'), '../');
});

test('rewriteDocLinkHref preserves anchors, queries, and external URLs', () => {
  assert.equal(rewriteDocLinkHref('reference/object-info.md#response-shape'), 'reference/object-info/#response-shape');
  assert.equal(rewriteDocLinkHref('../api/endpoints.md?view=full'), '../api/endpoints/?view=full');
  assert.equal(rewriteDocLinkHref('https://docs.comfy.org/custom-nodes/overview'), 'https://docs.comfy.org/custom-nodes/overview');
  assert.equal(rewriteDocLinkHref('#scope'), '#scope');
});

test('rewriteDocLinkHref preserves query-before-hash order after route rewriting', () => {
  assert.equal(
    rewriteDocLinkHref('reference/object-info.md?view=full#response-shape'),
    'reference/object-info/?view=full#response-shape',
  );
});

test('rewriteDocLinkHref preserves URL-encoded path segments', () => {
  assert.equal(
    rewriteDocLinkHref('reference/special%20topic.md'),
    'reference/special%20topic/',
  );
});

test('rewriteDocLinkHref normalizes backslashes and preserves combined query-plus-hash suffixes', () => {
  assert.equal(
    rewriteDocLinkHref('..\\reference\\version-pin-status.md?view=compact#automation'),
    '../reference/version-pin-status/?view=compact#automation',
  );
});

test('rewriteDocLinkHref rewrites current-directory and nested index markdown routes', () => {
  assert.equal(rewriteDocLinkHref('./index.md'), './');
  assert.equal(rewriteDocLinkHref('./reference/index.md#schema'), './reference/#schema');
});

test('rewriteDocLinkHref leaves non-markdown relative assets and mailto links unchanged', () => {
  assert.equal(rewriteDocLinkHref('../images/logo.svg'), '../images/logo.svg');
  assert.equal(rewriteDocLinkHref('mailto:docs@example.invalid'), 'mailto:docs@example.invalid');
});

test('stripLeadingH1 removes the first content H1 but preserves leading html banners', () => {
  const tree = {
    type: 'root',
    children: [
      { type: 'html', value: '<!-- GENERATED FILE: do not edit directly -->' },
      { type: 'heading', depth: 1, children: [{ type: 'text', value: 'Ecosystem Map' }] },
      { type: 'paragraph', children: [{ type: 'text', value: 'Summary.' }] },
    ],
  };

  stripLeadingH1(tree);

  assert.deepEqual(tree.children.map((node) => node.type), ['html', 'paragraph']);
});

test('stripLeadingH1 leaves later H1 nodes alone when earlier content exists', () => {
  const tree = {
    type: 'root',
    children: [
      { type: 'paragraph', children: [{ type: 'text', value: 'Intro.' }] },
      { type: 'heading', depth: 1, children: [{ type: 'text', value: 'Keep Me' }] },
    ],
  };

  stripLeadingH1(tree);

  assert.deepEqual(tree.children.map((node) => node.type), ['paragraph', 'heading']);
});

test('stripLeadingH1 ignores leading definitions before removing the first content H1', () => {
  const tree = {
    type: 'root',
    children: [
      { type: 'definition', identifier: 'ref', url: 'reference/glossary.md' },
      { type: 'heading', depth: 1, children: [{ type: 'text', value: 'Drop Me' }] },
      { type: 'paragraph', children: [{ type: 'text', value: 'Body.' }] },
    ],
  };

  stripLeadingH1(tree);

  assert.deepEqual(tree.children.map((node) => node.type), ['definition', 'paragraph']);
});

test('stripLeadingH1 removes an H1 after mixed skippable leading nodes', () => {
  const tree = {
    type: 'root',
    children: [
      { type: 'html', value: '<div>banner</div>' },
      { type: 'definition', identifier: 'ref', url: 'reference/glossary.md' },
      { type: 'heading', depth: 1, children: [{ type: 'text', value: 'Drop Me Too' }] },
      { type: 'paragraph', children: [{ type: 'text', value: 'Body.' }] },
    ],
  };

  stripLeadingH1(tree);

  assert.deepEqual(tree.children.map((node) => node.type), ['html', 'definition', 'paragraph']);
});

// Tests for currentFilePath-aware link resolution (fixes non-index page URL depth mismatch)
test('rewriteDocLinkHref resolves same-directory links to absolute paths with base when currentFilePath provided', () => {
  // From reference/glossary.md, link to source-evidence-policy.md should resolve to /comfyui-starchart/reference/source-evidence-policy/
  assert.equal(
    rewriteDocLinkHref('source-evidence-policy.md', 'reference/glossary.md'),
    '/comfyui-starchart/reference/source-evidence-policy/',
  );
});

test('rewriteDocLinkHref resolves parent-directory links to absolute paths with base when currentFilePath provided', () => {
  // From deep-dives/workflow-json-schema.md, link to ../api/prompt-submission.md should resolve to /comfyui-starchart/api/prompt-submission/
  assert.equal(
    rewriteDocLinkHref('../api/prompt-submission.md', 'deep-dives/workflow-json-schema.md'),
    '/comfyui-starchart/api/prompt-submission/',
  );
});

test('rewriteDocLinkHref resolves deeply nested relative links correctly', () => {
  // From start-here/nested/deep/page.md, link to ../../../reference/glossary.md should resolve to /comfyui-starchart/reference/glossary/
  assert.equal(
    rewriteDocLinkHref('../../../reference/glossary.md', 'start-here/nested/deep/page.md'),
    '/comfyui-starchart/reference/glossary/',
  );
});

test('rewriteDocLinkHref removes duplicate slashes when resolving current-file links', () => {
  assert.equal(
    rewriteDocLinkHref('reference//glossary.md', 'index.md'),
    '/comfyui-starchart/reference/glossary/',
  );
});

test('rewriteDocLinkHref resolved markdown routes always end with a slash before suffixes', () => {
  const rewritten = [
    rewriteDocLinkHref('reference/glossary.md'),
    rewriteDocLinkHref('reference/object-info.md?view=full'),
    rewriteDocLinkHref('reference/source-evidence-policy.md#trust'),
  ];

  assert.deepEqual(rewritten, [
    'reference/glossary/',
    'reference/object-info/?view=full',
    'reference/source-evidence-policy/#trust',
  ]);
});

test('rewriteDocLinkHref resolves index.md links to directory paths with base', () => {
  // From reference/glossary.md, link to ../api/index.md should resolve to /comfyui-starchart/api/
  assert.equal(
    rewriteDocLinkHref('../api/index.md', 'reference/glossary.md'),
    '/comfyui-starchart/api/',
  );
});

test('rewriteDocLinkHref preserves anchors when resolving with currentFilePath', () => {
  assert.equal(
    rewriteDocLinkHref('source-evidence-policy.md#trust-hierarchy', 'reference/glossary.md'),
    '/comfyui-starchart/reference/source-evidence-policy/#trust-hierarchy',
  );
});

test('rewriteDocLinkHref falls back to legacy behavior when currentFilePath is not provided', () => {
  // Without currentFilePath, should return relative path (legacy behavior for backward compatibility)
  assert.equal(rewriteDocLinkHref('source-evidence-policy.md'), 'source-evidence-policy/');
  assert.equal(rewriteDocLinkHref('../api/prompt-submission.md'), '../api/prompt-submission/');
});

test('rewriteDocLinkHref falls back to legacy behavior when currentFilePath is explicitly null', () => {
  // The remark plugin passes null via `|| null` fallback. Explicit null should behave
  // identically to undefined (falsy guard falls through to legacy path).
  assert.equal(rewriteDocLinkHref('source-evidence-policy.md', null), 'source-evidence-policy/');
  assert.equal(rewriteDocLinkHref('../api/prompt-submission.md', null), '../api/prompt-submission/');
});

test('rewriteDocLinkHref resolves relative links with root-level currentFilePath', () => {
  // When the current file is at content root (e.g., index.md or welcome.md),
  // currentDir becomes '' and the combined path is just the relative route path.
  assert.equal(
    rewriteDocLinkHref('start-here/author.md', 'index.md'),
    '/comfyui-starchart/start-here/author/',
  );
  assert.equal(
    rewriteDocLinkHref('reference/glossary.md', 'welcome.md'),
    '/comfyui-starchart/reference/glossary/',
  );
});

test('rewriteDocLinkHref resolves ./ prefixed relative links with currentFilePath', () => {
  // Links like ./other-page.md from a nested file should resolve relative to current dir.
  assert.equal(
    rewriteDocLinkHref('./service-integration.md', 'start-here/author.md'),
    '/comfyui-starchart/start-here/service-integration/',
  );
  assert.equal(
    rewriteDocLinkHref('./extension-developer.md#hooks', 'start-here/tooling-builder.md'),
    '/comfyui-starchart/start-here/extension-developer/#hooks',
  );
});
