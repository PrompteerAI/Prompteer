// Vitest configuration for web unit tests.
import { fileURLToPath } from "node:url";

import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  test: {
    coverage: {
      all: true,
      exclude: ["src/**/*.test.{ts,tsx}", "src/**/*.d.ts"],
      include: ["src/lib/**/*.{ts,tsx}", "src/server/**/*.{ts,tsx}"],
      provider: "v8",
      thresholds: {
        branches: 80,
        functions: 80,
        lines: 80,
        statements: 80,
      },
    },
    exclude: ["e2e/**", "node_modules/**", ".next/**"],
  },
});
