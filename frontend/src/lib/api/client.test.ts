import { describe, expect, it } from "vitest";

import { failure, json, setup } from "./test-support";

describe("api client", () => {
  it("returns the typed 200 body and sends Accept", async () => {
    const { client, fetchMock, lastHeaders } = setup(() =>
      json({ ai_assistant: false }),
    );
    const flags = await client.get("/api/v1/config/public-flags");
    expect(flags.ai_assistant).toBe(false);
    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "http://backend/api/v1/config/public-flags",
    );
    expect(lastHeaders().get("accept")).toBe("application/json");
  });

  it("evaluates a function base URL per request", async () => {
    let base = "http://one";
    const { client, fetchMock } = setup(() => json({ status: "ok" }), {
      baseUrl: () => base,
    });
    await client.get("/health/live");
    base = "http://two";
    await client.get("/health/live");
    expect(fetchMock.mock.calls.map((call) => call[0])).toEqual([
      "http://one/health/live",
      "http://two/health/live",
    ]);
  });

  it("returns documented non-200 results such as readiness 503", async () => {
    const { client } = setup(() =>
      json({ status: "not_ready" }, { status: 503 }),
    );
    const result = await client.getResult("/health/ready", [200, 503]);
    expect(result).toEqual({
      status: 503,
      ok: false,
      data: { status: "not_ready" },
    });
  });

  it("still throws for statuses that were not listed", async () => {
    const { client } = setup(() =>
      json({ title: "Boom", code: "internal_error" }, { status: 500 }),
    );
    const error = await failure(client.getResult("/health/ready", [200, 503]));
    expect(error.status).toBe(500);
  });

  it("attaches the CSRF token on unsafe methods only", async () => {
    const { client, lastHeaders } = setup(() => json({}), {
      csrfToken: () => "tok-1",
      credentials: "same-origin",
    });
    await client.request("POST", "/api/v1/x", { body: { a: 1 } });
    expect(lastHeaders().get("x-csrf-token")).toBe("tok-1");
    expect(lastHeaders().get("content-type")).toBe("application/json");
    for (const method of ["PUT", "PATCH", "DELETE"] as const) {
      await client.request(method, "/api/v1/x");
      expect(lastHeaders().get("x-csrf-token")).toBe("tok-1");
    }
    await client.get("/health/live");
    expect(lastHeaders().get("x-csrf-token")).toBeNull();
  });

  it("sends no token without a provider and sets credentials", async () => {
    const { client, lastHeaders, lastInit } = setup(() => json({}), {
      credentials: "same-origin",
    });
    await client.request("POST", "/api/v1/x", { body: {} });
    expect(lastHeaders().get("x-csrf-token")).toBeNull();
    expect(lastInit().credentials).toBe("same-origin");
  });

  it("handles 204 mutation responses", async () => {
    const { client } = setup(() => new Response(null, { status: 204 }));
    await expect(
      client.request("DELETE", "/api/v1/x"),
    ).resolves.toBeUndefined();
  });
});
