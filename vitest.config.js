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
      include: ['frontend/js/**/*.js'],
    },
  },
  resolve: {
    alias: {
      '/frontend': path.resolve(__dirname, './frontend'),
    },
  },
});
