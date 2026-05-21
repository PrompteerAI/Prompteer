// Browser fallback favicon route for clients that still request /favicon.ico.
const FAVICON_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#0f172a"/><path d="M18 19h28v6H18zM18 30h21v6H18zM18 41h14v6H18z" fill="#f8fafc"/><circle cx="45" cy="43" r="6" fill="#10b981"/></svg>`;

export function GET(): Response {
  return new Response(FAVICON_SVG, {
    headers: {
      "cache-control": "public, max-age=31536000, immutable",
      "content-type": "image/svg+xml",
    },
  });
}
