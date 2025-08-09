// frontend/vitest.config.ts

import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: true,
    // Add the exclude property below
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      '**/tests/**', // This line tells Vitest to ignore the Playwright E2E test folder
    ],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})