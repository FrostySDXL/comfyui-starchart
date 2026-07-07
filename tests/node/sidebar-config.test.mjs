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
  assert.deepEqual(sidebar.map((entry) => entry.label), [
    'Home',
    'Start Here',
    'Machine-Readable Reference',
    'API Reference',
    'Workflow and Architecture',
    'Hooks and Extensions',
    'Custom Nodes',
    'Advanced',
    'Repository Policy',
  ]);
  assert.equal(sidebar[0].label, 'Home');
  assert.equal(sidebar[0].slug, '');

  assert.deepEqual(
    sidebar[1].items.map((entry) => entry.slug),
    [
      'start-here/artifact-consumer',
      'start-here/tooling-builder',
      'start-here/service-integration',
      'start-here/extension-developer',
      'start-here/author',
    ],
  );
  assert.deepEqual(
    sidebar.find((entry) => entry.label === 'Machine-Readable Reference').items.map((entry) => entry.slug),
    [
      'reference/machine-readable-artifacts',
      'reference/artifact-schema-version-migration',
      'reference/version-pin-status',
      'reference/object-info',
    ],
  );
  assert.deepEqual(
    sidebar.find((entry) => entry.label === 'API Reference').items.map((entry) => entry.slug),
    ['api/endpoints', 'api/websocket', 'api/prompt-submission', 'api/history-queue'],
  );
  assert.deepEqual(
    sidebar.find((entry) => entry.label === 'Workflow and Architecture').items.map((entry) => entry.slug),
    ['deep-dives/workflow-json-schema', 'architecture/execution-pipeline', 'architecture/overview'],
  );
  assert.deepEqual(
    sidebar.find((entry) => entry.label === 'Hooks and Extensions').items.map((entry) => entry.slug),
    ['hooks/extension-points', 'hooks/javascript-hooks', 'hooks/server-hooks'],
  );
  assert.deepEqual(
    sidebar.find((entry) => entry.label === 'Custom Nodes').items.map((entry) => entry.slug),
    [
      'custom-nodes/development-guide',
      'custom-nodes/node-structure',
      'custom-nodes/registration',
      'custom-nodes/datatypes',
    ],
  );
  assert.deepEqual(
    sidebar.find((entry) => entry.label === 'Advanced').items.map((entry) => entry.slug),
    ['deep-dives/execution-model-inversion', 'deep-dives/registry-packaging-and-compatibility'],
  );

  const referenceSection = sidebar.find((entry) => entry.label === 'Repository Policy');
  assert.ok(referenceSection);
  assert.deepEqual(
    referenceSection.items.map((entry) => entry.slug),
    ['reference/source-evidence-policy', 'reference/topic-scope', 'reference/writing-style-guide'],
  );
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
