import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The React dev server proxies /api and /media to the local Django server so
// the offline-first app talks to one origin in dev as it will once packaged.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/media': 'http://127.0.0.1:8000',
    },
  },
})
