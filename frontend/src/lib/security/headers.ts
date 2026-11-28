/**
 * Security response headers for every route (NFR-SEC-008, SHOP-019).
 *
 * The CSP is nonce-free: nonces force dynamic rendering of every page, so
 * inline scripts are allowed with `'unsafe-inline'` for now. A nonce- or
 * hash-based policy is revisited in the M7 OWASP review (SHOP-082).
 * `upgrade-insecure-requests` and HSTS are deliberately absent: there is no
 * TLS locally, and both belong to the TLS-terminating edge (a later stage).
 */

export type SecurityHeader = { key: string; value: string };

export function contentSecurityPolicy({ dev }: { dev: boolean }): string {
  // `next dev` needs eval for React refresh and a WebSocket for HMR.
  const scriptSrc = dev
    ? "'self' 'unsafe-inline' 'unsafe-eval'"
    : "'self' 'unsafe-inline'";
  const connectSrc = dev ? "'self' ws:" : "'self'";
  return [
    "default-src 'self'",
    `script-src ${scriptSrc}`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self'",
    `connect-src ${connectSrc}`,
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "object-src 'none'",
  ].join("; ");
}

export function securityHeaders({ dev }: { dev: boolean }): SecurityHeader[] {
  return [
    { key: "Content-Security-Policy", value: contentSecurityPolicy({ dev }) },
    { key: "X-Content-Type-Options", value: "nosniff" },
    { key: "X-Frame-Options", value: "DENY" },
    { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
    {
      key: "Permissions-Policy",
      value: "camera=(), microphone=(), geolocation=()",
    },
    { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
  ];
}
