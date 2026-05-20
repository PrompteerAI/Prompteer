import baseConfig from "@prompteer/eslint-config/base";

export default [
  ...baseConfig,
  {
    ignores: ["dist/**"],
  },
];
