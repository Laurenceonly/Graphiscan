import { defineConfig } from 'vite';
import { fileURLToPath } from 'node:url';
export default defineConfig({ build: { rollupOptions: { input: Object.fromEntries(['index.html', 'download/index.html', 'about/index.html', 'privacy/index.html'].map(path => [path, fileURLToPath(new URL(path, import.meta.url))])) } } });
