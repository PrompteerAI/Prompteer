import nextConfig from "@prompteer/eslint-config/next";

export default [
  ...nextConfig,
  {
    ignores: ["dist/**"]
  }
];
