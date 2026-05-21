// next-intl navigation helpers. App links use locale-relative paths so another
// locale can reuse the same route definitions without hard-coded /en segments.
import { createNavigation } from "next-intl/navigation";

import { routing } from "./routing";

export const { Link, redirect, usePathname, useRouter, getPathname } =
  createNavigation(routing);
