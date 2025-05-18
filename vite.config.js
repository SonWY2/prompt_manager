import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig(({ mode }) => {
  // 환경변수에서 프론트엔드 포트 가져오기
  const PORT = process.env.VITE_PORT || 3030;
  const API_URL = process.env.VITE_API_URL || 'http://localhost:3000';

  return {
    plugins: [react()],
    server: {
      port: PORT,
      open: true,
      proxy: {
        '/api': {
          target: API_URL,
          changeOrigin: true,
          secure: false
        }
      }
    },
    build: {
      outDir: 'dist',
      emptyOutDir: true
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src')
      }
    },
    optimizeDeps: {
      include: ['react', 'react-dom', 'zustand']
    }
  };
});