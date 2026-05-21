// Next.js 15 discovers middleware.ts. Keep the implementation in proxy.ts so
// the project can remove this compatibility bridge after a Next 16 upgrade.
export { default } from "./proxy";

export const config = {
  matcher: ["/", "/((?!api|dev|_next|_vercel|.*\\..*).*)"],
};
