// Login screen for real Google OAuth and deterministic seed-user mock login.
import { LogIn, ShieldCheck, Sparkles, UserRound } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { Link } from "@/i18n/navigation";
import { localizedPath } from "@/i18n/paths";
import { signIn } from "@/lib/auth";
import { getServerEnv, publicEnv } from "@/lib/env";
import { safeLocalizedCallbackUrl } from "@/lib/redirects";

type Props = {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ callbackUrl?: string | string[] }>;
};

export default async function LoginPage({
  params,
  searchParams,
}: Props): Promise<React.ReactElement> {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  const redirectTo = safeLocalizedCallbackUrl(query.callbackUrl, locale);
  const isContinuation = redirectTo !== localizedPath("/", locale);

  async function signInWithGoogle(formData: FormData): Promise<void> {
    "use server";

    const loginHint = formData.get("login_hint");
    await signIn(
      "google",
      { redirectTo },
      typeof loginHint === "string" && loginHint.length > 0
        ? { login_hint: loginHint }
        : undefined,
    );
  }

  const t = await getTranslations("login");
  const serverEnv = getServerEnv();
  const useMockGoogle =
    publicEnv.NEXT_PUBLIC_USE_MOCK_GOOGLE &&
    !(serverEnv.GOOGLE_CLIENT_ID && serverEnv.GOOGLE_CLIENT_SECRET);
  const accounts = useMockGoogle
    ? [
        { email: "admin@prompteer.dev", label: t("admin"), Icon: ShieldCheck },
        { email: "paid@prompteer.dev", label: t("paid"), Icon: Sparkles },
        { email: "free@prompteer.dev", label: t("free"), Icon: UserRound },
      ]
    : [{ email: "", label: t("google"), Icon: LogIn }];

  return (
    <main className="grid min-h-screen place-items-center bg-zinc-50 px-6">
      <div className="w-full max-w-sm rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-zinc-950">{t("title")}</h1>
        {isContinuation ? (
          <p className="mt-3 text-sm leading-6 text-zinc-600">
            {t("continueDescription")}
          </p>
        ) : null}
        <form action={signInWithGoogle} className="mt-6 space-y-2">
          {accounts.map(({ email, label, Icon }) => (
            <button
              key={email || "google"}
              className="flex min-h-11 w-full items-center justify-center gap-2 rounded-md bg-zinc-950 px-4 text-sm font-medium text-white transition hover:bg-zinc-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-950"
              name="login_hint"
              type="submit"
              value={email}
            >
              <Icon aria-hidden="true" className="h-4 w-4 shrink-0" />
              <span>{label}</span>
            </button>
          ))}
        </form>
        <Link
          className="mt-4 inline-flex min-h-11 items-center text-sm font-medium text-zinc-700 underline underline-offset-4 hover:text-zinc-950"
          href="/"
        >
          {t("home")}
        </Link>
      </div>
    </main>
  );
}
