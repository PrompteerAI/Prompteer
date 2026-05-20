// Server-side logging wrapper for Next.js route handlers. It keeps web log
// metadata aligned with the API service without exposing secrets to the client.
import pino from "pino";

import { getServerEnv } from "./env";

type WebLogger = pino.Logger;

let cachedLogger: WebLogger | undefined;

export function getWebLogger(): WebLogger {
  if (cachedLogger) {
    return cachedLogger;
  }

  const serverEnv = getServerEnv();
  cachedLogger = pino({
    level: "info",
    base: {
      service: "prompteer-web",
      version: serverEnv.APP_VERSION,
      env: serverEnv.ENV,
    },
    timestamp: pino.stdTimeFunctions.isoTime,
  });
  return cachedLogger;
}
