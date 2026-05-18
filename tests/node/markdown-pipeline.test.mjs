import test from 'node:test';
import assert from 'node:assert/strict';

import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkStringify from 'remark-stringify';

import {
  remarkRewriteDocLinks,
  remarkStripLeadingH1,
} from '../../src/site/markdown.js';

test('remarkRewriteDocLinks rewrites markdown links in a real remark pipeline', async () => {
  const input = '[Artifacts](reference/machine-readable-artifacts.md) and [Anchored](../api/endpoints.md#prompt)';

  const output = String(
    await unified()
      .use(remarkParse)
      .use(remarkRewriteDocLinks)
      .use(remarkStringify)
      .process(input),
  );

  assert.match(output, /reference\/machine-readable-artifacts\//);
  assert.match(output, /\.\.\/api\/endpoints\/#prompt/);
});

test('remarkStripLeadingH1 removes the first heading in a real remark pipeline', async () => {
  const input = '<!-- GENERATED FILE: do not edit directly -->\n\n# Keep Out\n\nBody paragraph.';

  const output = String(
    await unified()
      .use(remarkParse)
      .use(remarkStripLeadingH1)
      .use(remarkStringify)
      .process(input),
  );

  assert.doesNotMatch(output, /^# Keep Out/m);
  assert.match(output, /Body paragraph\./);
  assert.match(output, /GENERATED FILE/);
});

test('remark plugins compose cleanly in one pipeline', async () => {
  const input = '# Page Title\n\nSee [Queue](../api/history-queue.md).';

  const output = String(
    await unified()
      .use(remarkParse)
      .use(remarkStripLeadingH1)
      .use(remarkRewriteDocLinks)
      .use(remarkStringify)
      .process(input),
  );

  assert.doesNotMatch(output, /^# Page Title/m);
  assert.match(output, /\.\.\/api\/history-queue\//);
});
