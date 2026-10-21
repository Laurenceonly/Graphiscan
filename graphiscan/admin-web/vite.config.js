import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: { dedupe: ['vue', 'vue-router'] },
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true
  }
})
