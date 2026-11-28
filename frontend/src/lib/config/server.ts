import "server-only";

const DEFAULT_BACKEND_INTERNAL_URL = "http://127.0.0.1:8000";

export type ServerConfig = {
  /** Absolute origin-and-path of the backend, without a trailing slash. */
  backendInternalUrl: string;
};

export class ConfigurationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ConfigurationError";
  }
}

function parseBackendUrl(raw: string): string {
  // The value is never echoed: it could contain credentials.
  const invalid = new ConfigurationError(
    "BACKEND_INTERNAL_URL must be an absolute http(s) URL without credentials, query or fragment.",
  );
  let url: URL;
  try {
    url = new URL(raw);
  } catch {
    throw invalid;
  }
  const hasExtras =
    url.username !== "" ||
    url.password !== "" ||
    url.search !== "" ||
    url.hash !== "" ||
    raw.includes("?") ||
    raw.includes("#");
  if (!["http:", "https:"].includes(url.protocol) || hasExtras) {
    throw invalid;
  }
  return url.href.replace(/\/+$/, "");
}

/**
 * Reads the server configuration from the environment at call time, so a
 * container can set it at runtime. Server-only: never import in client code.
 */
export function getServerConfig(
  env: Record<string, string | undefined> = process.env,
): ServerConfig {
  const raw = env.BACKEND_INTERNAL_URL?.trim();
  return {
    backendInternalUrl: parseBackendUrl(raw || DEFAULT_BACKEND_INTERNAL_URL),
  };
}
