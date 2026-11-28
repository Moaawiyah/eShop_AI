import { describe, expect, it } from "vitest";

import { ConfigurationError, getServerConfig } from "./server";

describe("getServerConfig", () => {
  it("defaults to the local backend when unset or blank", () => {
    expect(getServerConfig({}).backendInternalUrl).toBe(
      "http://127.0.0.1:8000",
    );
    expect(
      getServerConfig({ BACKEND_INTERNAL_URL: "  " }).backendInternalUrl,
    ).toBe("http://127.0.0.1:8000");
  });

  it("normalizes trailing slashes", () => {
    expect(
      getServerConfig({ BACKEND_INTERNAL_URL: "http://backend:8000/" })
        .backendInternalUrl,
    ).toBe("http://backend:8000");
    expect(
      getServerConfig({ BACKEND_INTERNAL_URL: "https://api.internal/base//" })
        .backendInternalUrl,
    ).toBe("https://api.internal/base");
  });

  it("reads the environment at call time", () => {
    const env: Record<string, string | undefined> = {};
    expect(getServerConfig(env).backendInternalUrl).toBe(
      "http://127.0.0.1:8000",
    );
    env.BACKEND_INTERNAL_URL = "http://other:9";
    expect(getServerConfig(env).backendInternalUrl).toBe("http://other:9");
  });

  it.each([
    "not a url",
    "/relative",
    "ftp://backend:21",
    "http://user:secret@backend:8000",
    "http://backend:8000?x=1",
    "http://backend:8000/?",
    "http://backend:8000#frag",
  ])("rejects %s without echoing it", (value) => {
    try {
      getServerConfig({ BACKEND_INTERNAL_URL: value });
      expect.unreachable();
    } catch (error) {
      expect(error).toBeInstanceOf(ConfigurationError);
      expect((error as Error).message).not.toContain("secret");
      expect((error as Error).message).toContain("BACKEND_INTERNAL_URL");
    }
  });
});
