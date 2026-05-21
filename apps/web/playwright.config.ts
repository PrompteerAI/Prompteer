// Playwright configuration for Compose-backed end-to-end acceptance coverage.
import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.PLAYWRIGHT_BASE_URL || "http://localhost";

export default defineConfig({
  testDir: "./e2e",
  workers: process.env.CI ? 1 : undefined,
  use: {
    baseURL,
    screenshot: "only-on-failure",
    trace: "on-first-retry",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
