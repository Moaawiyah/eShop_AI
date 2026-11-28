/** Shared helpers for the API client tests. */
import { expect, vi } from "vitest";

import { createApiClient } from "./client";
import { ApiError } from "./errors";

export function json(
  body: unknown,
  init: ResponseInit = {},
  type = "application/json",
) {
  return new Response(JSON.stringify(body), {
    ...init,
    headers: { "Content-Type": type, ...init.headers },
  });
}

export function setup(
  respond: () => Response | Promise<Response>,
  options: Partial<Parameters<typeof createApiClient>[0]> = {},
) {
  const fetchMock = vi.fn<typeof fetch>(async () => respond());
  const client = createApiClient({
    baseUrl: "http://backend",
    fetch: fetchMock,
    ...options,
  });
  const lastInit = () => fetchMock.mock.calls.at(-1)?.[1] as RequestInit;
  const lastHeaders = () => new Headers(lastInit().headers);
  return { client, fetchMock, lastInit, lastHeaders };
}

export async function failure(promise: Promise<unknown>): Promise<ApiError> {
  try {
    await promise;
  } catch (error) {
    expect(error).toBeInstanceOf(ApiError);
    return error as ApiError;
  }
  throw new Error("expected the request to fail");
}
