// Locale routing configuration. Locale tags are generated from message files.
import { defineRouting } from "next-intl/routing";

import { defaultLocale, locales } from "./locales.generated";

export const routing = defineRouting({
  locales,
  defaultLocale,
});
