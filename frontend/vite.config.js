import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],

  server: {
    host: "0.0.0.0",
    port: 5173,

    allowedHosts: [
      "localhost",
      "127.0.0.1",
      ".replit.dev",
      ".replit.app",
      ".repl.co",
    ],

    proxy: {
      "/api": {
        target: process.env.BACKEND_URL || "http://127.0.0.1:5001",
        changeOrigin: true,
      },
    },
  },
});