import {
  errorFromResponse,
  invalidResponseError,
  networkError,
  timeoutError,
} from "./errors";
import type {
  ApiResult,
  CsrfTokenProvider,
  DocumentedStatus,
  GetResponse,
  PathsWithGet,
  RequestOptions,
} from "./types";

export const DEFAULT_TIMEOUT_MS = 5_000;

const UNSAFE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export type ApiClientOptions = {
  /** Base URL, or a function evaluated per request (runtime configuration). */
  baseUrl: string | (() => string);
  fetch?: typeof fetch;
  /** Browser only: sends the session cookie to the same origin. */
  credentials?: RequestCredentials;
  /** Supplies the CSRF token for unsafe methods (arrives with SHOP-032). */
  csrfToken?: CsrfTokenProvider;
  timeoutMs?: number;
};

export type MutationRequest = RequestOptions & { body?: unknown };

export type ApiClient = ReturnType<typeof createApiClient>;

function isTimeout(error: unknown): boolean {
  // Structural: DOMException is not an `Error` instance in every runtime.
  return (
    typeof error === "object" &&
    error !== null &&
    "name" in error &&
    error.name === "TimeoutError"
  );
}

/**
 * The single typed API client core. Types come from the generated OpenAPI
 * schema; errors are normalized to `ApiError`. Isomorphic: it imports no
 * server-only module (see `server-client.ts` and `browser-client.ts`).
 */
export function createApiClient(options: ApiClientOptions) {
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;

  async function send(
    method: string,
    path: string,
    { body, signal, timeoutMs: timeout }: MutationRequest = {},
  ): Promise<Response> {
    const base =
      typeof options.baseUrl === "function"
        ? options.baseUrl()
        : options.baseUrl;
    const headers = new Headers({ Accept: "application/json" });
    if (body !== undefined) headers.set("Content-Type", "application/json");
    if (UNSAFE_METHODS.has(method)) {
      const token = options.csrfToken?.();
      if (token) headers.set("X-CSRF-Token", token);
    }
    const timeoutSignal = AbortSignal.timeout(timeout ?? timeoutMs);
    try {
      return await (options.fetch ?? fetch)(`${base}${path}`, {
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
        credentials: options.credentials,
        cache: "no-store",
        signal: signal
          ? AbortSignal.any([signal, timeoutSignal])
          : timeoutSignal,
      });
    } catch (error) {
      if (signal?.aborted) throw error; // caller cancelled: not an API failure
      throw isTimeout(error) ? timeoutError() : networkError();
    }
  }

  async function readJson<T>(response: Response): Promise<T> {
    try {
      return (await response.json()) as T; // typed by the OpenAPI schema
    } catch {
      throw invalidResponseError(response.status);
    }
  }

  /** GET a path and return its typed 200 body; any other status throws. */
  async function get<P extends PathsWithGet>(
    path: P,
    request?: RequestOptions,
  ): Promise<GetResponse<P>> {
    const response = await send("GET", path, request);
    if (!response.ok) throw await errorFromResponse(response);
    return readJson<GetResponse<P>>(response);
  }

  /**
   * GET where the listed statuses (documented with a JSON body, e.g. the 503
   * of `/health/ready`) are results rather than errors. Others still throw.
   */
  async function getResult<
    P extends PathsWithGet,
    S extends DocumentedStatus<P>,
  >(
    path: P,
    statuses: readonly S[],
    request?: RequestOptions,
  ): Promise<ApiResult<P, S>> {
    const response = await send("GET", path, request);
    if (!(statuses as readonly number[]).includes(response.status)) {
      throw await errorFromResponse(response);
    }
    const data = await readJson<unknown>(response);
    return { status: response.status, ok: response.ok, data } as ApiResult<
      P,
      S
    >;
  }

  /** Untyped-path request for mutations; typed per endpoint when they exist. */
  async function request<T = unknown>(
    method: "POST" | "PUT" | "PATCH" | "DELETE",
    path: string,
    init?: MutationRequest,
  ): Promise<T> {
    const response = await send(method, path, init);
    if (!response.ok) throw await errorFromResponse(response);
    if (response.status === 204) return undefined as T;
    return readJson<T>(response);
  }

  return { get, getResult, request };
}
