import { LogIn, ShieldCheck, Sparkles, UserRound } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { signIn } from "@/lib/auth";

async function signInWithGoogle(formData: FormData): Promise<void> {
  "use server";

  const loginHint = formData.get("login_hint");
  await signIn(
    "google",
    { redirectTo: "/en" },
    typeof loginHint === "string" && loginHint.length > 0
      ? { login_hint: loginHint }
      : undefined,
  );
}

export default async function LoginPage(): Promise<React.ReactElement> {
  const t = await getTranslations("login");
  const useMockGoogle =
    process.env.NEXT_PUBLIC_USE_MOCK_GOOGLE !== "false" &&
    !(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET);
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
        <form action={signInWithGoogle} className="mt-6 space-y-2">
          {accounts.map(({ email, label, Icon }) => (
            <button
              key={email || "google"}
              className="flex h-10 w-full items-center justify-center gap-2 rounded-md bg-zinc-950 px-4 text-sm font-medium text-white transition hover:bg-zinc-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-950"
              name="login_hint"
              type="submit"
              value={email}
            >
              <Icon aria-hidden="true" className="h-4 w-4 shrink-0" />
              <span>{label}</span>
            </button>
          ))}
        </form>
      </div>
    </main>
  );
}
