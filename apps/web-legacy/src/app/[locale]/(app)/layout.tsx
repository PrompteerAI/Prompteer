// Legacy app routes intentionally stay reachable without a local Auth.js server.
export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}): React.ReactElement {
  return <>{children}</>;
}
