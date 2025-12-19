import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import fs from "fs";

// Пути к сертификатам
const keyPath = "/app/certs/localhost.key";
const certPath = "/app/certs/localhost.crt";

let httpsConfig = undefined;

// Если оба файла существуют — включаем HTTPS
if (fs.existsSync(keyPath) && fs.existsSync(certPath)) {
  httpsConfig = {
    key: fs.readFileSync(keyPath),
    cert: fs.readFileSync(certPath),
  };
}

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: "localhost",
    port: 3000,
    proxy: {
      "/v1": {
        target: "http://app:8050",
        changeOrigin: true,
      },
    },
    https: httpsConfig, // undefined → HTTP, объект → HTTPS
  },
});
