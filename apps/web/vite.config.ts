import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  base: process.env.VITE_BASE_PATH ?? "/",
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    host: true,
    proxy: { "/api": process.env.VITE_API_PROXY ?? "http://localhost:8000", "/health": process.env.VITE_API_PROXY ?? "http://localhost:8000" },
  },
  preview: { port: 5173, host: true },
});
