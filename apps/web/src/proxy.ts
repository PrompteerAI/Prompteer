// Locale routing proxy for Next.js App Router. Redirects the root path into the
// configured next-intl locale segment before route handlers run.
import createMiddleware from "next-intl/middleware";

import { routing } from "./i18n/routing";

export default createMiddleware(routing);

export const config = {
  matcher: ["/", "/((?!api|dev|_next|_vercel|.*\\..*).*)"],
};
