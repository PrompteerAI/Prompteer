// Lightweight client-side toast provider for rate-limit and workflow notices.
"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";

import { cn } from "@/lib/cn";

type ToastVariant = "info" | "warning" | "error" | "success";

type ToastInput = {
  title: string;
  description?: string;
  variant?: ToastVariant;
};

type ToastRecord = ToastInput & {
  id: number;
  variant: ToastVariant;
};

type ToastContextValue = {
  toast: (input: ToastInput) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

const variantStyles: Record<ToastVariant, string> = {
  error: "border-red-200 bg-red-50 text-red-950",
  info: "border-zinc-200 bg-white text-zinc-950",
  success: "border-emerald-200 bg-emerald-50 text-emerald-950",
  warning: "border-amber-200 bg-amber-50 text-amber-950",
};

export function ToastProvider({
  children,
}: {
  children: React.ReactNode;
}): React.ReactElement {
  const [toasts, setToasts] = useState<ToastRecord[]>([]);

  const toast = useCallback((input: ToastInput) => {
    const id = Date.now() + Math.floor(Math.random() * 1_000);
    const nextToast = {
      id,
      variant: input.variant ?? "info",
      title: input.title,
      description: input.description,
    };
    setToasts((current) => [...current.slice(-2), nextToast]);
    window.setTimeout(() => {
      setToasts((current) => current.filter((item) => item.id !== id));
    }, 6_000);
  }, []);

  const value = useMemo(() => ({ toast }), [toast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        aria-live="polite"
        className="fixed right-4 top-4 z-50 flex w-[min(24rem,calc(100vw-2rem))] flex-col gap-3"
      >
        {toasts.map((item) => (
          <div
            key={item.id}
            className={cn(
              "rounded-md border px-4 py-3 text-sm shadow-lg",
              variantStyles[item.variant],
            )}
            role={item.variant === "error" ? "alert" : "status"}
          >
            <p className="font-semibold">{item.title}</p>
            {item.description ? (
              <p className="mt-1 leading-5 opacity-90">{item.description}</p>
            ) : null}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used inside ToastProvider.");
  }
  return context;
}
