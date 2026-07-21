import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // 生产构建守卫：VITE_API_BASE_URL 必须显式配置且指向真实后端，
  // 否则前端会 fallback 到 http://localhost:8000 导致线上整站调用失败。
  if (mode === 'production') {
    const env = loadEnv(mode, __dirname, 'VITE_')
    const base = env.VITE_API_BASE_URL
    if (!base || /localhost|127\.0\.0\.1/.test(base)) {
      throw new Error(
        `[构建中止] 生产构建要求 VITE_API_BASE_URL 指向真实后端地址，当前为: ${base || '(未设置)'}。\n` +
        `请在 frontend/.env.production 中设置，例如 VITE_API_BASE_URL=https://paper.example.com`
      )
    }
  }

  return {
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          'element-plus': ['element-plus'],
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'charts': ['echarts', 'vue-echarts']
        }
      }
    }
  }
  }
})
