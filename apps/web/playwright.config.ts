import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  retries: 0,
  use: { baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173", trace: "retain-on-failure" },
  webServer: {
    command: "npm run dev",
    url: "http://localhost:5173",
    reuseExistingServer: true,
    env: { VITE_API_PROXY: process.env.VITE_API_PROXY ?? "http://localhost:8000" },
  },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
});
