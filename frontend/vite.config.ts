import { fileURLToPath, URL } from "node:url"

import vue from "@vitejs/plugin-vue"
import { defineConfig } from "vite"
import electron from 'vite-plugin-electron/simple'

export default defineConfig({
  plugins: [
    vue(),
    electron({
      main: {
        entry: 'electron/main.ts',
      },
      preload: {
        input: 'electron/preload.ts',
      },
    }),
  ],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 5173,
    strictPort: true,
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('vue') || id.includes('pinia') || id.includes('vue-router') || id.includes('@vueuse')) {
              return 'vue-vendor'
            }
            if (id.includes('element-plus') || id.includes('@element-plus')) {
              return 'element-plus'
            }
            if (id.includes('html2pdf.js') || id.includes('marked') || id.includes('lucide-vue-next')) {
              return 'feature-vendor'
            }
            return 'vendor'
          }

          if (id.includes('/src/views/PrintingPage/') || id.includes('/src/views/PrintingPage.vue')) {
            return 'printing'
          }
          if (id.includes('/src/views/ProctoringPage/') || id.includes('/src/views/ProctoringPage.vue')) {
            return 'proctoring'
          }
          if (id.includes('/src/views/RoomsPage/') || id.includes('/src/views/RoomsPage.vue')) {
            return 'rooms'
          }
          return undefined
        },
      },
    },
  },
})

