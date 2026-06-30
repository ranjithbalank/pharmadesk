import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The React dev server proxies /api and /media to the local Django server so
// the offline-first app talks to one origin in dev as it will once packaged.
export default defineConfig(({ command }) => ({
  plugins: [react()],
  // The packaged desktop build is served by Django/WhiteNoise under /static/,
  // so build defaults to that base. A Vercel build sets VITE_BASE=/ to serve
  // the SPA from the domain root. The dev server always stays at '/'.
  base: process.env.VITE_BASE ?? (command === 'build' ? '/static/' : '/'),
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/media': 'http://127.0.0.1:8000',
    },
  },
}))
