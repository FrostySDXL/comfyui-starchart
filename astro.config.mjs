// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { remarkRewriteDocLinks, remarkStripLeadingH1 } from './src/site/markdown.js';
import { loadSidebarData, toStarlightSidebar } from './src/site/sidebar.js';

// https://astro.build/config
export default defineConfig({
  site: 'https://frostysdxl.github.io/comfyui_knowledge_base',
  base: '/comfyui_knowledge_base/',
  outDir: './dist',
  publicDir: './public',
  markdown: {
    remarkPlugins: [remarkRewriteDocLinks, remarkStripLeadingH1],
  },
  integrations: [
    starlight({
      title: 'ComfyUI Knowledge Base',
      social: [
        {
          icon: 'github',
          label: 'GitHub',
          href: 'https://github.com/FrostySDXL/comfyui_knowledge_base',
        },
      ],
      sidebar: toStarlightSidebar(loadSidebarData()),
    }),
  ],
});
