// Locale root layout for the legacy-preview app.
import type { Metadata } from "next";
import { hasLocale } from "next-intl";
import { NextIntlClientProvider } from "next-intl";
import { getMessages } from "next-intl/server";
import { notFound } from "next/navigation";

import { LegacyFooter } from "@/components/legacy/footer";
import { LegacyHeader } from "@/components/legacy/header";
import { routing } from "@/i18n/routing";
import { readGatewaySession } from "@/lib/auth-gateway";

import "../globals.css";

type Props = {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
};

export const metadata: Metadata = {
  title: "Prompteer Legacy Preview",
  description: "Legacy-style Prompteer frontend preview",
};

export default async function LocaleLayout({
  children,
  params,
}: Props): Promise<React.ReactElement> {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }
  const [messages, session] = await Promise.all([
    getMessages(),
    readGatewaySession(),
  ]);

  return (
    <html lang={locale}>
      <body>
        <NextIntlClientProvider messages={messages}>
          <div className="legacy-app">
            <LegacyHeader locale={locale} session={session} />
            {children}
            <LegacyFooter />
          </div>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
