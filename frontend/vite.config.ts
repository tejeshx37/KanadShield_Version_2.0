import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'node:path'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: false, // served from public/manifest.webmanifest directly
      workbox: {
        // App shell (JS/CSS/HTML) is precached with a content-hash-based,
        // versioned strategy managed by Workbox — old caches are purged on
        // each new deploy. API responses are explicitly NOT cached here:
        // offline access to specific documents/summaries is handled by
        // IndexedDB (src/lib/offlineCache.ts), which lets the UI say
        // precisely what's available offline instead of silently serving
        // a stale API cache that could imply full coverage.
        globPatterns: ['**/*.{js,css,html,svg}'],
        navigateFallback: '/index.html',
        runtimeCaching: [],
      },
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
