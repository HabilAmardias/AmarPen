import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [
    sveltekit({
      adapter: adapter({
        fallback: 'index.html',
        strict: false
      })
    })
  ],
  resolve: {
    conditions: ['browser']
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    include: ['tests/unit/**/*.test.ts'],
    globals: true,
    css: false,
    coverage: {
      provider: 'istanbul',
      reporter: ['text', 'json', 'html'],
      reportsDirectory: './coverage',
      include: ['src/**/*.{ts,svelte}'],
      exclude: ['src/app.d.ts', 'src/routes/**/+layout.ts', 'src/**/+page.ts', 'src/**/+layout.ts', 'src/routes/+error.svelte'],
      thresholds: {
        statements: 85,
        branches: 50,
        functions: 75,
        lines: 85
      }
    }
  }
});
