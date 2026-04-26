import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  server: {
    port: 5174,
    strictPort: false
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
});
