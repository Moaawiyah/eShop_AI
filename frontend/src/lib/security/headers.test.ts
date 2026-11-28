import { describe, expect, it } from "vitest";

import { contentSecurityPolicy, securityHeaders } from "./headers";

function header(dev: boolean, key: string): string | undefined {
  return securityHeaders({ dev }).find((h) => h.key === key)?.value;
}

describe("securityHeaders", () => {
  it.each([false, true])("sets the static headers (dev=%s)", (dev) => {
    expect(header(dev, "X-Content-Type-Options")).toBe("nosniff");
    expect(header(dev, "X-Frame-Options")).toBe("DENY");
    expect(header(dev, "Referrer-Policy")).toBe(
      "strict-origin-when-cross-origin",
    );
    expect(header(dev, "Cross-Origin-Opener-Policy")).toBe("same-origin");
    expect(header(dev, "Permissions-Policy")).toBe(
      "camera=(), microphone=(), geolocation=()",
    );
  });

  it("does not set HSTS (the TLS edge owns it)", () => {
    expect(header(false, "Strict-Transport-Security")).toBeUndefined();
  });
});

describe("contentSecurityPolicy", () => {
  it("is strict in production", () => {
    const csp = contentSecurityPolicy({ dev: false });
    for (const directive of [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob:",
      "font-src 'self'",
      "connect-src 'self'",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "object-src 'none'",
    ]) {
      expect(csp.split("; ")).toContain(directive);
    }
    expect(csp).not.toContain("unsafe-eval");
    expect(csp).not.toContain("ws:");
    expect(csp).not.toContain("upgrade-insecure-requests");
  });

  it("allows eval and WebSocket HMR only in development", () => {
    const csp = contentSecurityPolicy({ dev: true });
    expect(csp).toContain("script-src 'self' 'unsafe-inline' 'unsafe-eval'");
    expect(csp).toContain("connect-src 'self' ws:");
    expect(csp).toContain("frame-ancestors 'none'");
  });
});
