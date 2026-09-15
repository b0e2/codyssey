import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 라이브러리는 거의 바뀌지 않는다. 앱 코드와 나눠 두면
// 화면을 고쳐 배포해도 방문자가 라이브러리를 다시 받지 않는다.
function vendorChunk(id) {
  if (!id.includes('node_modules')) return undefined
  if (id.includes('@supabase')) return 'supabase'
  if (id.includes('react')) return 'react'
  return 'vendor'
}

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: { manualChunks: vendorChunk },
    },
  },
})
