/** Pure helpers for the `/api/v1/*` proxy route (kept out of `route.ts`). */

export const REQUEST_HEADERS = [
  "accept",
  "content-type",
  "cookie",
  // Forwarded so the backend can verify the browser origin (SHOP-019).
  "origin",
  "x-csrf-token",
  "x-request-id",
] as const;

export const RESPONSE_HEADERS = [
  "content-type",
  "cache-control",
  "set-cookie",
  "x-request-id",
  "allow",
  "retry-after",
  "location",
] as const;

export function filterHeaders(
  source: Headers,
  allowed: readonly string[],
): Headers {
  const result = new Headers();
  for (const name of allowed) {
    const value = source.get(name);
    if (value !== null) result.set(name, value);
  }
  return result;
}

/** Rejects empty, `.`, `..` and separator-bearing segments (path traversal). */
export function isSafeSegments(segments: readonly string[]): boolean {
  return (
    segments.length > 0 &&
    segments.every(
      (segment) =>
        segment !== "" &&
        segment !== "." &&
        segment !== ".." &&
        !/[/\\\u0000]/.test(segment),
    )
  );
}

export function buildUpstreamUrl(
  backend: string,
  segments: readonly string[],
  search: string,
): string {
  const path = segments.map(encodeURIComponent).join("/");
  return `${backend}/api/v1/${path}${search}`;
}

function problem(
  status: number,
  title: string,
  code: string,
  detail: string,
): Response {
  return Response.json(
    { type: "about:blank", title, status, code, detail },
    {
      status,
      headers: {
        "Content-Type": "application/problem+json",
        "Cache-Control": "no-store",
      },
    },
  );
}

export function badRequest(): Response {
  return problem(400, "Bad Request", "bad_request", "The request is invalid.");
}

export function badGateway(): Response {
  return problem(
    502,
    "Bad Gateway",
    "backend_unavailable",
    "The service is temporarily unavailable.",
  );
}
