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

test('rewriteDocLinkHref rewrites legacy markdown links and preserves suffixes/non-page links', () => {
  const cases = [
    ['reference/machine-readable-artifacts.md', 'reference/machine-readable-artifacts/'],
    ['../api/endpoints.md', '../api/endpoints/'],
    ['tutorials/index.md', 'tutorials/'],
    ['../index.md', '../'],
    ['reference/object-info.md#response-shape', 'reference/object-info/#response-shape'],
    ['../api/endpoints.md?view=full', '../api/endpoints/?view=full'],
    ['https://docs.comfy.org/custom-nodes/overview', 'https://docs.comfy.org/custom-nodes/overview'],
    ['#scope', '#scope'],
    ['reference/object-info.md?view=full#response-shape', 'reference/object-info/?view=full#response-shape'],
    ['reference/special%20topic.md', 'reference/special%20topic/'],
    ['..\\reference\\version-pin-status.md?view=compact#automation', '../reference/version-pin-status/?view=compact#automation'],
    ['./index.md', './'],
    ['./reference/index.md#schema', './reference/#schema'],
    ['../images/logo.svg', '../images/logo.svg'],
    ['mailto:docs@example.invalid', 'mailto:docs@example.invalid'],
    ['source-evidence-policy.md', 'source-evidence-policy/'],
    ['../api/prompt-submission.md', '../api/prompt-submission/'],
  ];

  for (const [href, expected] of cases) {
    assert.equal(rewriteDocLinkHref(href), expected, href);
  }
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

test('rewriteDocLinkHref resolves currentFilePath-aware links to absolute site paths', () => {
  const cases = [
    ['source-evidence-policy.md', 'reference/glossary.md', '/comfyui-starchart/reference/source-evidence-policy/'],
    ['../api/prompt-submission.md', 'deep-dives/workflow-json-schema.md', '/comfyui-starchart/api/prompt-submission/'],
    ['../../../reference/glossary.md', 'start-here/nested/deep/page.md', '/comfyui-starchart/reference/glossary/'],
    ['reference//glossary.md', 'index.md', '/comfyui-starchart/reference/glossary/'],
    ['../api/index.md', 'reference/glossary.md', '/comfyui-starchart/api/'],
    ['source-evidence-policy.md#trust-hierarchy', 'reference/glossary.md', '/comfyui-starchart/reference/source-evidence-policy/#trust-hierarchy'],
    ['source-evidence-policy.md', null, 'source-evidence-policy/'],
    ['../api/prompt-submission.md', null, '../api/prompt-submission/'],
    ['start-here/author.md', 'index.md', '/comfyui-starchart/start-here/author/'],
    ['reference/glossary.md', 'welcome.md', '/comfyui-starchart/reference/glossary/'],
    ['./service-integration.md', 'start-here/author.md', '/comfyui-starchart/start-here/service-integration/'],
    ['./extension-developer.md#hooks', 'start-here/tooling-builder.md', '/comfyui-starchart/start-here/extension-developer/#hooks'],
  ];

  for (const [href, currentFilePath, expected] of cases) {
    assert.equal(rewriteDocLinkHref(href, currentFilePath), expected, `${currentFilePath}: ${href}`);
  }
});
