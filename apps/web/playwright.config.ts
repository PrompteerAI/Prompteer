// Playwright configuration for Compose-backed end-to-end acceptance coverage.
import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.PLAYWRIGHT_BASE_URL || "http://localhost";
const isCI = Boolean(process.env.CI);

export default defineConfig({
  expect: {
    timeout: isCI ? 10_000 : 5_000,
  },
  reporter: isCI ? [["github"], ["list"]] : "list",
  retries: isCI ? 2 : 0,
  testDir: "./e2e",
  timeout: isCI ? 45_000 : 30_000,
  workers: isCI ? 1 : undefined,
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
