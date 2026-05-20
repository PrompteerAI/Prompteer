// Shared ESLint flat config for Next.js applications.
import nextPlugin from "@next/eslint-plugin-next";

import baseConfig from "./base.mjs";

const nextCoreWebVitals = {
  ...nextPlugin.flatConfig.coreWebVitals,
  settings: {
    next: {
      rootDir: ".",
    },
  },
};

export default [...baseConfig, nextCoreWebVitals];
