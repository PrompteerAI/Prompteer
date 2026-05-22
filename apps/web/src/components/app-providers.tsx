// Client-side provider shell for TanStack Query and future browser contexts.
"use client";

// Client-only providers shared by localized app routes.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

import { ToastProvider } from "@/components/ui";

export function AppProviders({
  children,
}: {
  children: React.ReactNode;
}): React.ReactElement {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          mutations: {
            retry: false,
          },
          queries: {
            refetchOnWindowFocus: false,
            retry: 1,
            staleTime: 30_000,
          },
        },
      }),
  );

  return (
    <ToastProvider>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </ToastProvider>
  );
}
