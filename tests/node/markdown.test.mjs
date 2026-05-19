import test from 'node:test';
import assert from 'node:assert/strict';

import {
  rewriteDocLinkHref,
  stripLeadingH1,
} from '../../src/site/markdown.js';

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
