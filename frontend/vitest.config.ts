import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts', './src/test/jsdom-setup.ts'],
    include: ['src/**/__tests__/**'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json'],
      reportsDirectory: './coverage',
      include: ['src/**/*.{ts,vue}'],
      exclude: [
        // bootstrap entrypoints
        'src/main.ts',
        // Type-only declarations (no runtime code)
        'src/**/*.d.ts',
        // barrel / type-only files
        'src/**/index.ts',
        'src/types/**',
        // Vite env types
        'src/vite-env.d.ts',
      ],
      thresholds: {
        // Phase 0 commitment: lines + statements at 95%. The Vue
        // Coverage v8 provider counts the many tiny one-line event
        // handlers and setup-style computed getters as "functions"
        // even when they only forward to a Pinia store; that's why
        // the function ratio stays in the low 70s even with broad
        // integration coverage. We accept 70% for that one and
        // 83% branches to account for unreachable intersection-observer
        // paths in jsdom. Phase 1 (FastAPI refactor) will require
        // re-tooling the frontend anyway.
        lines: 95,
        functions: 70,
        branches: 83,
        statements: 95,
      },
      // Show uncovered lines so the gaps are easy to spot.
      reportOnFailure: true,
      skipFull: false,
    },
  },
})