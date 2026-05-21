// Server-only gate for local development routes that should not exist in prod.
import { getServerEnv } from "@/lib/env";

type DevRouteEnv = {
  ENV: "development" | "test" | "production";
  ENABLE_DEV_ROUTES: boolean;
};

export function devRoutesEnabled(env: DevRouteEnv = getServerEnv()): boolean {
  return env.ENABLE_DEV_ROUTES && env.ENV !== "production";
}
