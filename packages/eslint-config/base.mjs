// Shared ESLint flat config for TypeScript packages.
import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default [
  {
    ignores: [
      "*.config.ts",
      "*.tsbuildinfo",
      ".next/**",
      "coverage/**",
      "next-env.d.ts",
      "playwright-report/**",
      "test-results/**",
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommendedTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: {
          allowDefaultProject: ["*.config.mjs"],
        },
      },
    },
  },
];
