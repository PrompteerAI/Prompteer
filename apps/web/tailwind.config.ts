// Tailwind compatibility config for editor tooling and shared design tokens.
import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        accent: "var(--accent)",
        "accent-foreground": "var(--accent-foreground)",
        background: "var(--background)",
        border: "var(--border)",
        destructive: "var(--destructive)",
        "destructive-foreground": "var(--destructive-foreground)",
        foreground: "var(--foreground)",
        muted: "var(--muted)",
        primary: "var(--primary)",
        "primary-foreground": "var(--primary-foreground)",
        ring: "var(--ring)",
        surface: "var(--surface)",
        "surface-subtle": "var(--surface-subtle)",
      },
    },
  },
} satisfies Config;
