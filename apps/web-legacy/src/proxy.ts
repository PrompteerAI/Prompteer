// Locale routing proxy for the legacy preview.
import createMiddleware from "next-intl/middleware";

import { routing } from "./i18n/routing";

export default createMiddleware(routing);

export const config = {
  matcher: ["/", "/((?!api|dev|_next|_vercel|.*\\..*).*)"],
};
