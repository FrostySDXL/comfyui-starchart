import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';

import {
  docPathToSlug,
  loadSidebarData,
  toStarlightSidebar,
} from '../../src/site/sidebar.js';

test('docPathToSlug maps root, section index, and page paths deterministically', () => {
  assert.equal(docPathToSlug('index.md'), '');
  assert.equal(docPathToSlug('hooks/index.md'), 'hooks');
  assert.equal(docPathToSlug('reference/glossary.md'), 'reference/glossary');
});

test('loadSidebarData returns checked-in sidebar entries', () => {
  const sidebarData = loadSidebarData();
  assert.ok(Array.isArray(sidebarData));
  assert.equal(sidebarData[0].label, 'Home');
  assert.equal(sidebarData[1].label, 'Start Here');
});

test('loadSidebarData reports file read errors with path context', () => {
  const missingPath = join(tmpdir(), 'missing-sidebar-data.json');

  assert.throws(() => loadSidebarData(missingPath), {
    message: new RegExp(`Failed to read sidebar data at ${missingPath.replaceAll('\\', '\\\\')}:`),
  });
});

test('loadSidebarData reports malformed JSON with path context', () => {
  const dir = mkdtempSync(join(tmpdir(), 'sidebar-json-'));
  const malformedPath = join(dir, 'sidebar-data.json');
  writeFileSync(malformedPath, '[{"label": "Broken"}', 'utf8');

  try {
    assert.throws(() => loadSidebarData(malformedPath), {
      message: new RegExp(`Failed to parse sidebar data JSON at ${malformedPath.replaceAll('\\', '\\\\')}:`),
    });
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('loadSidebarData rejects non-array JSON with a clear error', () => {
  const dir = mkdtempSync(join(tmpdir(), 'sidebar-json-'));
  const nonArrayPath = join(dir, 'sidebar-data.json');
  writeFileSync(nonArrayPath, '{"label": "Broken"}', 'utf8');

  try {
    assert.throws(() => loadSidebarData(nonArrayPath), {
      message: new RegExp(`Sidebar data at ${nonArrayPath.replaceAll('\\', '\\\\')} must be a top-level array`),
    });
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('toStarlightSidebar converts checked-in paths to Starlight sidebar items', () => {
  const sidebar = toStarlightSidebar(loadSidebarData());
  assert.equal(sidebar[0].label, 'Home');
  assert.equal(sidebar[0].slug, '');
  assert.equal(sidebar[1].items[0].slug, 'start-here/author');

  const referenceSection = sidebar.find((entry) => entry.label === 'Reference');
  assert.ok(referenceSection);
  const topicScopeEntry = referenceSection.items.find((entry) => entry.label === 'Topic Scope');
  assert.equal(topicScopeEntry.slug, 'reference/topic-scope');
});

test('toStarlightSidebar normalizes backslash paths and derives fallback labels deterministically', () => {
  const sidebar = toStarlightSidebar([
    {
      label: 'Reference',
      items: [{ path: 'reference\\version-pin-status.md' }],
    },
  ]);

  assert.equal(sidebar[0].items[0].label, 'Version Pin Status');
  assert.equal(sidebar[0].items[0].slug, 'reference/version-pin-status');
});

test('docPathToSlug rejects non-markdown sidebar paths', () => {
  assert.throws(() => docPathToSlug('reference/version-pin-status.json'), {
    message: /must end in \.md/,
  });
});

test('toStarlightSidebar rejects invalid leaf entries', () => {
  assert.throws(() => toStarlightSidebar([{ label: 'Broken' }]), {
    message: /Invalid sidebar entry/,
  });
});

test('toStarlightSidebar converts a larger nested sidebar shape deterministically', () => {
  const sidebar = toStarlightSidebar([
    { path: 'index.md', label: 'Home' },
    {
      label: 'Reference',
      items: [
        { path: 'reference/index.md' },
        { path: 'reference/source-evidence-policy.md' },
        {
          label: 'Hooks',
          items: [{ path: 'hooks/javascript-hooks.md' }],
        },
      ],
    },
  ]);

  assert.deepEqual(sidebar, [
    { label: 'Home', slug: '' },
    {
      label: 'Reference',
      items: [
        { label: 'Index', slug: 'reference' },
        { label: 'Source Evidence Policy', slug: 'reference/source-evidence-policy' },
        {
          label: 'Hooks',
          items: [{ label: 'Javascript Hooks', slug: 'hooks/javascript-hooks' }],
        },
      ],
    },
  ]);
});
