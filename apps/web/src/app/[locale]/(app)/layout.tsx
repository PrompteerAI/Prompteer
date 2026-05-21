// Protected app route-group layout. Public marketing/login routes live outside
// this group; every product surface here requires an Auth.js session.
import { redirect } from "next/navigation";

import { auth } from "@/lib/auth";

type Props = {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
};

export default async function AppLayout({
  children,
  params,
}: Props): Promise<React.ReactElement> {
  const session = await auth();
  if (!session?.user) {
    const { locale } = await params;
    redirect(`/${locale}/login`);
  }

  return <>{children}</>;
}
