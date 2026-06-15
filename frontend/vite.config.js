import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// ===================================================================
// API TARGET CONFIGURATION
// ===================================================================
// Set VITE_API_TARGET before building to point the frontend at a
// remote backend (production / cloud deployment).
//
// Examples:
//   $env:VITE_API_TARGET="https://api.your-domain.com"; npm run build
//   VITE_API_TARGET=http://123.45.67.89:5000 npm run build
//
// If NOT set, the frontend uses '/api' (same-origin) which works
// when Flask serves both frontend and backend from the same process.
// ===================================================================

const API_TARGET = process.env.VITE_API_TARGET || ''
const BUILD_API_BASE = API_TARGET ? `${API_TARGET}/api` : '/api'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  // Inject __API_BASE__ as a global constant so request.js can use it
  // without importing a Vite-specific module (which wouldn't work in
  // the browser).
  define: {
    __API_BASE__: JSON.stringify(BUILD_API_BASE),
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: API_TARGET || 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
})
