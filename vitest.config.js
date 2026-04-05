import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./frontend/tests/setup.js'],
    exclude: ['tests/e2e/**', 'node_modules/**', 'dist/**'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['frontend/js/**/*.js'],
      exclude: ['frontend/js/vendor/**', 'frontend/tests/**'],
    },
  },
  resolve: {
    alias: {
      '/frontend': path.resolve(__dirname, './frontend'),
    },
  },
});
