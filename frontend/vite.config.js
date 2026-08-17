import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    // Lets `npm run dev` talk straight to a backend running on the host
    // (e.g. `uvicorn app.main:app --reload` from backend/) without CORS
    // config or nginx in the loop. Production always goes through nginx.
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
