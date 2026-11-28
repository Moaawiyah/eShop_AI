import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DELETE, GET, HEAD, POST } from "./route";

const fetchMock = vi.fn<typeof fetch>();

function context(...path: string[]) {
  return { params: Promise.resolve({ path }) };
}

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  vi.stubEnv("BACKEND_INTERNAL_URL", "http://backend:8000/");
  vi.spyOn(console, "error").mockImplementation(() => undefined);
});

afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
  vi.restoreAllMocks();
});

describe("API proxy route", () => {
  it("forwards method, path and query to the backend", async () => {
    fetchMock.mockResolvedValue(Response.json({ ai_assistant: false }));
    const response = await GET(
      new Request("http://web/api/v1/config/public-flags?a=1&b=x%20y"),
      context("config", "public-flags"),
    );
    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ ai_assistant: false });
    const [url, init] = fetchMock.mock.calls[0] ?? [];
    expect(url).toBe(
      "http://backend:8000/api/v1/config/public-flags?a=1&b=x%20y",
    );
    expect(init?.method).toBe("GET");
    expect(init?.body).toBeUndefined();
  });

  it("forwards bodies for unsafe methods", async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }));
    const response = await POST(
      new Request("http://web/api/v1/things", {
        method: "POST",
        body: JSON.stringify({ a: 1 }),
        headers: { "content-type": "application/json" },
      }),
      context("things"),
    );
    expect(response.status).toBe(204);
    const init = fetchMock.mock.calls[0]?.[1];
    expect(init?.method).toBe("POST");
    expect(init?.body).toBeDefined();
    const deleted = await DELETE(
      new Request("http://web/api/v1/things/1", { method: "DELETE" }),
      context("things", "1"),
    );
    expect(deleted.status).toBe(204);
    expect(fetchMock.mock.calls[1]?.[1]?.method).toBe("DELETE");
  });

  it("forwards HEAD without a body", async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 200 }));
    await HEAD(
      new Request("http://web/api/v1/x", { method: "HEAD" }),
      context("x"),
    );
    expect(fetchMock.mock.calls[0]?.[1]?.method).toBe("HEAD");
  });

  it("forwards only allow-listed request headers", async () => {
    fetchMock.mockResolvedValue(Response.json({}));
    await GET(
      new Request("http://web/api/v1/x", {
        headers: {
          accept: "application/json",
          cookie: "sid=1",
          "x-csrf-token": "t",
          "x-request-id": "rid",
          "content-type": "application/json",
          authorization: "Bearer secret",
          host: "evil.example",
          "x-forwarded-for": "1.2.3.4",
        },
      }),
      context("x"),
    );
    const sent = new Headers(fetchMock.mock.calls[0]?.[1]?.headers);
    expect([...sent.keys()].sort()).toEqual([
      "accept",
      "content-type",
      "cookie",
      "x-csrf-token",
      "x-request-id",
    ]);
  });

  it("returns only allow-listed response headers and every Set-Cookie", async () => {
    const upstream = new Response("{}", {
      status: 201,
      headers: {
        "content-type": "application/json",
        "cache-control": "no-store",
        "x-request-id": "rid",
        "retry-after": "5",
        allow: "GET",
        location: "/api/v1/x/1",
        server: "uvicorn",
        "x-internal": "yes",
      },
    });
    upstream.headers.append("set-cookie", "a=1; HttpOnly");
    upstream.headers.append("set-cookie", "b=2; HttpOnly");
    fetchMock.mockResolvedValue(upstream);
    const response = await GET(
      new Request("http://web/api/v1/x"),
      context("x"),
    );
    expect(response.status).toBe(201);
    expect(response.headers.get("server")).toBeNull();
    expect(response.headers.get("x-internal")).toBeNull();
    expect(response.headers.get("x-request-id")).toBe("rid");
    expect(response.headers.get("cache-control")).toBe("no-store");
    expect(response.headers.get("retry-after")).toBe("5");
    expect(response.headers.get("allow")).toBe("GET");
    expect(response.headers.get("location")).toBe("/api/v1/x/1");
    expect(response.headers.getSetCookie()).toEqual([
      "a=1; HttpOnly",
      "b=2; HttpOnly",
    ]);
  });

  it.each([
    [[""]],
    [["."]],
    [[".."]],
    [["a", "..", "b"]],
    [["a/b"]],
    [["a\\b"]],
    [[]],
  ])("rejects unsafe path segments %j with 400", async (segments) => {
    const response = await GET(
      new Request("http://web/api/v1/x"),
      context(...segments),
    );
    expect(response.status).toBe(400);
    expect(response.headers.get("content-type")).toBe(
      "application/problem+json",
    );
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("returns a 502 problem without internal details when the backend is unreachable", async () => {
    fetchMock.mockRejectedValue(
      new TypeError("connect ECONNREFUSED 10.0.0.5:8000"),
    );
    const response = await GET(
      new Request("http://web/api/v1/x?q=1"),
      context("x"),
    );
    expect(response.status).toBe(502);
    expect(response.headers.get("content-type")).toBe(
      "application/problem+json",
    );
    const text = await response.text();
    expect(JSON.parse(text)).toEqual({
      type: "about:blank",
      title: "Bad Gateway",
      status: 502,
      code: "backend_unavailable",
      detail: "The service is temporarily unavailable.",
    });
    expect(text).not.toMatch(/10\.0\.0\.5|ECONNREFUSED|backend:8000/);
    const logged = vi.mocked(console.error).mock.calls.flat().join(" ");
    expect(logged).not.toMatch(/10\.0\.0\.5|q=1|backend:8000/);
  });

  it("returns 502 for an invalid backend configuration", async () => {
    vi.stubEnv("BACKEND_INTERNAL_URL", "ftp://nope");
    const response = await GET(
      new Request("http://web/api/v1/x"),
      context("x"),
    );
    expect(response.status).toBe(502);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
