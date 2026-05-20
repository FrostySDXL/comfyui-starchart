// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { remarkRewriteDocLinks, remarkStripLeadingH1 } from './src/site/markdown.js';
import { loadSidebarData, toStarlightSidebar } from './src/site/sidebar.js';

// https://astro.build/config
export default defineConfig({
  site: 'https://frostysdxl.github.io/comfyui-starchart',
  base: '/comfyui-starchart/',
  outDir: './dist',
  publicDir: './public',
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
          href: 'https://github.com/FrostySDXL/comfyui-starchart',
        },
      ],
      sidebar: toStarlightSidebar(loadSidebarData()),
    }),
  ],
});
