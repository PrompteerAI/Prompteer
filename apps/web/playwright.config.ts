import { defineConfig, devices } from "@playwright/test";

const reuseExistingServer = !process.env.CI;

export default defineConfig({
  testDir: "./e2e",
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command:
        "bash -lc 'cd ../api && AUTO_SEED_ON_STARTUP=false uv run fastapi dev app/main.py --port 8000'",
      url: "http://127.0.0.1:8000/api/v1/health/live",
      reuseExistingServer,
      timeout: 120_000,
    },
    {
      command: "pnpm dev",
      url: "http://localhost:3000",
      reuseExistingServer,
      timeout: 120_000,
    },
  ],
});
