// ESLint flat config for generated and hand-written shared type exports.
import baseConfig from "@prompteer/eslint-config/base";

export default [
  ...baseConfig,
  {
    ignores: ["dist/**"],
  },
];
