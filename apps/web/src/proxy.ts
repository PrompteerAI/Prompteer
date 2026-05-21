// Locale routing proxy for Next.js App Router. It also preserves the originally
// requested protected path for signed-out users before route handlers run.
import { hasLocale } from "next-intl";
import createMiddleware from "next-intl/middleware";
import { NextResponse, type NextRequest } from "next/server";

import { routing } from "./i18n/routing";

const handleI18nRouting = createMiddleware(routing);
const protectedSegments = new Set([
  "billing",
  "board",
  "challenges",
  "profile",
]);
const authSessionCookies = [
  "authjs.session-token",
  "__Secure-authjs.session-token",
];

export default function proxy(request: NextRequest): NextResponse {
  const signedOutRedirect = redirectSignedOutProtectedRequest(request);
  if (signedOutRedirect) {
    return signedOutRedirect;
  }

  return handleI18nRouting(request);
}

function redirectSignedOutProtectedRequest(
  request: NextRequest,
): NextResponse | null {
  const [, locale, segment] = request.nextUrl.pathname.split("/");

  if (
    !locale ||
    !segment ||
    !hasLocale(routing.locales, locale) ||
    !protectedSegments.has(segment) ||
    hasAuthSessionCookie(request)
  ) {
    return null;
  }

  const loginUrl = request.nextUrl.clone();
  const callbackUrl = `${request.nextUrl.pathname}${request.nextUrl.search}`;
  loginUrl.pathname = `/${locale}/login`;
  loginUrl.search = "";
  loginUrl.searchParams.set("callbackUrl", callbackUrl);

  return NextResponse.redirect(loginUrl);
}

function hasAuthSessionCookie(request: NextRequest): boolean {
  return authSessionCookies.some((cookieName) =>
    request.cookies.has(cookieName),
  );
}

export const config = {
  matcher: ["/", "/((?!api|dev|_next|_vercel|.*\\..*).*)"],
};
