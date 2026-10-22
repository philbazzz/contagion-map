import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// VITE_BASE: GitHub project Pages needs "/<repo>/" ; local preview can use "./"
const base = process.env.VITE_BASE || "./";

export default defineConfig({
  base,
  plugins: [react()],
  server: {
    port: 5173,
    // Optional local FastAPI when VITE_API_MODE=http
    proxy: { "/api": { target: "http://127.0.0.1:8000", changeOrigin: true } },
  },
  preview: { port: 4173 },
});
