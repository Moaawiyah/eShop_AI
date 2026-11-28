import { getServerConfig } from "@/lib/config/server";

import {
  badGateway,
  badRequest,
  buildUpstreamUrl,
  filterHeaders,
  isSafeSegments,
  REQUEST_HEADERS,
  RESPONSE_HEADERS,
} from "./upstream";

/**
 * Same-origin proxy for `/api/v1/*` (ARCHITECTURE 6.5). A route handler, not
 * `rewrites`: the backend URL is read from the environment at request time,
 * which `rewrites` (fixed at build time in standalone output) cannot do.
 * Only `/api/v1/*` is proxied; `/health/*` is never exposed.
 */
const UPSTREAM_TIMEOUT_MS = 10_000;

type Context = { params: Promise<{ path: string[] }> };

async function proxy(request: Request, { params }: Context): Promise<Response> {
  const { path } = await params;
  if (!isSafeSegments(path)) return badRequest();

  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  try {
    const url = buildUpstreamUrl(
      getServerConfig().backendInternalUrl,
      path,
      new URL(request.url).search,
    );
    const upstream = await fetch(url, {
      method: request.method,
      headers: filterHeaders(request.headers, REQUEST_HEADERS),
      body: hasBody ? request.body : undefined,
      // Required by Node when streaming a request body.
      ...(hasBody ? { duplex: "half" } : {}),
      redirect: "manual",
      cache: "no-store",
      signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
    });
    const headers = filterHeaders(upstream.headers, RESPONSE_HEADERS);
    // `Headers` joins multiple Set-Cookie values; keep them separate.
    headers.delete("set-cookie");
    for (const cookie of upstream.headers.getSetCookie()) {
      headers.append("set-cookie", cookie);
    }
    return new Response(upstream.body, { status: upstream.status, headers });
  } catch {
    // Short message only: URLs and errors may contain internal details.
    console.error("API proxy: backend request failed");
    return badGateway();
  }
}

export {
  proxy as DELETE,
  proxy as GET,
  proxy as HEAD,
  proxy as PATCH,
  proxy as POST,
  proxy as PUT,
};
