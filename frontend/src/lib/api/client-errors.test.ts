import { describe, expect, it } from "vitest";

import { ApiError } from "./errors";
import { failure, json, setup } from "./test-support";

describe("api client errors", () => {
  it("normalizes problem+json errors", async () => {
    const { client } = setup(() =>
      json(
        {
          type: "x",
          title: "Validation Error",
          status: 422,
          detail: "Bad input.",
          code: "validation_error",
          correlation_id: "abc-123",
          errors: [{ field: "email", code: "missing" }, { nope: 1 }],
        },
        { status: 422, headers: { "X-Request-ID": "header-id" } },
        "application/problem+json",
      ),
    );
    const error = await failure(client.get("/api/v1/config/public-flags"));
    expect(error).toMatchObject({
      status: 422,
      code: "validation_error",
      title: "Validation Error",
      detail: "Bad input.",
      correlationId: "abc-123",
      fieldErrors: [{ field: "email", code: "missing" }],
    });
  });

  it("falls back to the X-Request-ID header for the correlation id", async () => {
    const { client } = setup(() =>
      json(
        { title: "Nope" },
        { status: 404, headers: { "X-Request-ID": "rid" } },
      ),
    );
    const error = await failure(client.get("/api/v1/config/public-flags"));
    expect(error.correlationId).toBe("rid");
    expect(error.code).toBe("http_error");
  });

  it("uses generic values for non-JSON error bodies and never leaks them", async () => {
    const { client } = setup(
      () =>
        new Response("<html>stack trace secret-token</html>", {
          status: 500,
          headers: { "Content-Type": "text/html" },
        }),
    );
    const error = await failure(client.get("/api/v1/config/public-flags"));
    expect(error.status).toBe(500);
    expect(error.code).toBe("http_error");
    expect(`${error.message} ${error.detail}`).not.toContain("secret-token");
  });

  it("uses generic values for malformed JSON error bodies", async () => {
    const { client } = setup(
      () =>
        new Response("{broken", {
          status: 500,
          headers: { "Content-Type": "application/problem+json" },
        }),
    );
    const error = await failure(client.get("/api/v1/config/public-flags"));
    expect(error.code).toBe("http_error");
  });

  it("reports an invalid 200 body", async () => {
    const { client } = setup(
      () =>
        new Response("not json", {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
    );
    const error = await failure(client.get("/api/v1/config/public-flags"));
    expect(error.code).toBe("invalid_response");
  });

  it("maps network failures to status 0 network_error", async () => {
    const { client } = setup(() => {
      throw new TypeError("fetch failed: http://internal:8000");
    });
    const error = await failure(client.get("/health/live"));
    expect(error).toMatchObject({ status: 0, code: "network_error" });
    expect(error.message).not.toContain("internal");
  });

  it("maps timeouts to status 0 timeout", async () => {
    const { client } = setup(() => {
      throw new DOMException("timed out", "TimeoutError");
    });
    const error = await failure(client.get("/health/live"));
    expect(error).toMatchObject({ status: 0, code: "timeout" });
  });

  it("aborts with a timeout signal and honours the override", async () => {
    const { client, lastInit } = setup(() => json({ status: "ok" }));
    await client.get("/health/live", { timeoutMs: 1 });
    expect(lastInit().signal).toBeInstanceOf(AbortSignal);
  });

  it("rethrows the caller's own abort instead of an ApiError", async () => {
    const controller = new AbortController();
    const { client } = setup(() => {
      controller.abort();
      throw new DOMException("aborted", "AbortError");
    });
    await expect(
      client.get("/health/live", { signal: controller.signal }),
    ).rejects.not.toBeInstanceOf(ApiError);
  });
});
