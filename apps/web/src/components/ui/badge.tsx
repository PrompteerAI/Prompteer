// Shadcn-style badge primitive for compact status and category labels.
import type { HTMLAttributes, ReactElement } from "react";

import { cn } from "@/lib/cn";

type BadgeVariant =
  | "default"
  | "secondary"
  | "outline"
  | "destructive"
  | "success"
  | "warning";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

const badgeVariants: Record<BadgeVariant, string> = {
  default: "border-transparent bg-primary text-primary-foreground",
  destructive: "border-transparent bg-destructive text-destructive-foreground",
  outline: "border-border bg-transparent text-foreground",
  secondary: "border-transparent bg-surface-subtle text-foreground",
  success: "border-emerald-200 bg-emerald-50 text-emerald-900",
  warning: "border-amber-200 bg-amber-50 text-amber-900",
};

export function Badge({
  className,
  variant = "default",
  ...props
}: BadgeProps): ReactElement {
  return (
    <span
      className={cn(
        "inline-flex h-6 items-center rounded-md border px-2 text-xs font-semibold leading-none",
        badgeVariants[variant],
        className,
      )}
      {...props}
    />
  );
}
