import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: ['smartparkingiot.us-east-1.elasticbeanstalk.com'],
    proxy: {
      '/api': {
        target: 'https://l9hs049p42.execute-api.us-east-1.amazonaws.com',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
