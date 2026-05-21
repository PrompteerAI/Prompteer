// Next.js 15 compatibility bridge; Next 16 can discover proxy.ts directly.
export { default } from "./proxy";

export const config = {
  matcher: ["/", "/((?!api|dev|_next|_vercel|.*\\..*).*)"],
};
