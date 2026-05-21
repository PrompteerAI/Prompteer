// Shadcn-style button primitive for shared command and link-like controls.
import type { ButtonHTMLAttributes, ReactElement } from "react";
import { forwardRef } from "react";

import { cn } from "@/lib/cn";

type ButtonVariant =
  | "default"
  | "secondary"
  | "outline"
  | "ghost"
  | "destructive";
type ButtonSize = "sm" | "md" | "lg" | "icon";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  size?: ButtonSize;
  variant?: ButtonVariant;
}

const buttonVariants: Record<ButtonVariant, string> = {
  default:
    "border-transparent bg-primary text-primary-foreground hover:bg-teal-800",
  destructive:
    "border-transparent bg-destructive text-destructive-foreground hover:bg-red-800",
  ghost:
    "border-transparent bg-transparent text-foreground hover:bg-surface-subtle",
  outline: "border-border bg-surface text-foreground hover:bg-surface-subtle",
  secondary:
    "border-transparent bg-surface-subtle text-foreground hover:bg-border",
};

const buttonSizes: Record<ButtonSize, string> = {
  icon: "size-10 p-0",
  lg: "h-12 px-5 text-base",
  md: "h-10 px-4 text-sm",
  sm: "h-8 px-3 text-sm",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  function Button(
    { className, size = "md", type = "button", variant = "default", ...props },
    ref,
  ): ReactElement {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center gap-2 rounded-md border font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
          buttonVariants[variant],
          buttonSizes[size],
          className,
        )}
        type={type}
        {...props}
      />
    );
  },
);
