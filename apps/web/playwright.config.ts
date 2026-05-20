import { defineConfig, devices } from "@playwright/test";

const reuseExistingServer = !process.env.CI;
const apiCommand =
  "bash -lc 'cd ../api && mkdir -p ../../.verify/e2e && rm -f ../../.verify/e2e/api.sqlite && api_db=$(pwd)/../../.verify/e2e/api.sqlite && DATABASE_URL=sqlite:///${api_db} AUTO_SEED_ON_STARTUP=true uv run fastapi dev app/main.py --port 8000'";

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
      command: apiCommand,
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
