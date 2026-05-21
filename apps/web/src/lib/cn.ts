// Small class-name combiner for local UI primitives without adding a dependency.
export function cn(
  ...classes: Array<string | false | null | undefined>
): string {
  return classes.filter(Boolean).join(" ");
}
