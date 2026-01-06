import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: parseInt(process.env.VITE_PORT || '5173'),
    strictPort: true, // Fail immediately if port is in use (for reproducibility)
    proxy: {
      '/api': {
        // VITE_API_URL: for Docker (http://dev-backend:8000)
        // localhost: for local development
        target: process.env.VITE_API_URL || `http://localhost:${process.env.POLYHEAR_PORT || 8000}`,
        changeOrigin: true,
      },
    },
  },
})
