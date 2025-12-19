import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import fs from "fs";
// https://vite.dev/config/

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/v1": {
        target: "http://app:8050",
        changeOrigin: true,
      },
    },
    https: {
      key: fs.readFileSync("/app/certs/localhost.key"),
      cert: fs.readFileSync("/app/certs/localhost.crt"),
    },
    host: "localhost",
    port: 3000,
  },
});

