import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: "list",
  timeout: 30_000,
  expect: { timeout: 10_000 },

  use: {
    baseURL: "http://localhost:3001",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  /* The backend (port 8000) and frontend (port 3001) must be running. */
  webServer: [
    {
      command: "cd .. && source venv/bin/activate && uvicorn backend.main:app --port 8000",
      port: 8000,
      reuseExistingServer: true,
      timeout: 10_000,
    },
    {
      command: "npm run dev -- --port 3001",
      port: 3001,
      reuseExistingServer: true,
      timeout: 15_000,
    },
  ],
});
