import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default [
  {
    ignores: ["*.config.mjs", "*.config.ts", "eslint.config.mjs", ".next/**", "next-env.d.ts"]
  },
  js.configs.recommended,
  ...tseslint.configs.recommendedTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true
      }
    }
  }
];
