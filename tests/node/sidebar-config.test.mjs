import test from 'node:test';
import assert from 'node:assert/strict';

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

test('toStarlightSidebar converts checked-in paths to Starlight sidebar items', () => {
  const sidebar = toStarlightSidebar(loadSidebarData());
  assert.equal(sidebar[0].label, 'Home');
  assert.equal(sidebar[0].slug, '');
  assert.equal(sidebar[1].items[0].slug, 'start-here/author');

  const orientationSection = sidebar.find((entry) => entry.label === 'Orientation');
  assert.ok(orientationSection);
  const glossaryEntry = orientationSection.items.find((entry) => entry.label === 'Glossary');
  assert.equal(glossaryEntry.slug, 'reference/glossary');
});
