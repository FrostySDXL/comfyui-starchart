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
