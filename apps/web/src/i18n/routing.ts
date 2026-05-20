// Locale routing configuration. English is the only shipped locale at launch.
import { defineRouting } from "next-intl/routing";

export const routing = defineRouting({
  locales: ["en"],
  defaultLocale: "en",
});
