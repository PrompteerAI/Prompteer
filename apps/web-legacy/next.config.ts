// Next.js configuration for the legacy-preview frontend.
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const nextConfig = withNextIntl({});

export default nextConfig;
