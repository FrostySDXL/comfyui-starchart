// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { remarkRewriteDocLinks, remarkStripLeadingH1 } from './src/site/markdown.js';
import { loadSidebarData, toStarlightSidebar } from './src/site/sidebar.js';
import siteConfig from './src/site/site-config.json' with { type: 'json' };

const REPO_URL = 'https://github.com/FrostySDXL/comfyui-starchart';

// https://astro.build/config
export default defineConfig({
  site: siteConfig.site,
  base: siteConfig.base,
  outDir: './dist',
  publicDir: './public',
  build: {
    format: 'directory',
  },
  markdown: {
    remarkPlugins: [remarkRewriteDocLinks, remarkStripLeadingH1],
  },
  integrations: [
    starlight({
      title: 'ComfyUI StarChart',
      social: [
        {
          icon: 'github',
          label: 'GitHub',
          href: REPO_URL,
        },
      ],
      editLink: {
        baseUrl: `${REPO_URL}/edit/main/`,
      },
      lastUpdated: true,
      disable404Route: true,
      sidebar: toStarlightSidebar(loadSidebarData()),
    }),
  ],
});
