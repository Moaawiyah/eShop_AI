export type FieldError = { field: string; code: string };

type ApiErrorInit = {
  status: number;
  code: string;
  title: string;
  detail: string;
  correlationId?: string | null;
  fieldErrors?: readonly FieldError[];
};

/** The single error type thrown by the API client (problem+json normalized). */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly title: string;
  readonly detail: string;
  readonly correlationId: string | null;
  readonly fieldErrors: readonly FieldError[];

  constructor(init: ApiErrorInit) {
    // Only normalized, safe strings: never a raw response body.
    super(`${init.title} (${init.code})`);
    this.name = "ApiError";
    this.status = init.status;
    this.code = init.code;
    this.title = init.title;
    this.detail = init.detail;
    this.correlationId = init.correlationId ?? null;
    this.fieldErrors = init.fieldErrors ?? [];
  }
}

const MAX_TEXT = 300;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function text(value: unknown, fallback: string): string {
  return typeof value === "string" && value !== ""
    ? value.slice(0, MAX_TEXT)
    : fallback;
}

function parseFieldErrors(value: unknown): FieldError[] {
  if (!Array.isArray(value)) return [];
  return value.flatMap((item): FieldError[] =>
    isRecord(item) &&
    typeof item.field === "string" &&
    typeof item.code === "string"
      ? [
          {
            field: item.field.slice(0, MAX_TEXT),
            code: item.code.slice(0, MAX_TEXT),
          },
        ]
      : [],
  );
}

/** Builds an ApiError from a failed response; the body is untrusted input. */
export async function errorFromResponse(response: Response): Promise<ApiError> {
  const headerId = response.headers.get("x-request-id");
  const generic = {
    status: response.status,
    code: "http_error",
    title: "Request failed",
    detail: "The request could not be completed.",
    correlationId: headerId,
  };
  const contentType = response.headers.get("content-type") ?? "";
  if (!/\bjson\b/i.test(contentType)) return new ApiError(generic);
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    return new ApiError(generic);
  }
  if (!isRecord(body)) return new ApiError(generic);
  const correlation =
    typeof body.correlation_id === "string" && body.correlation_id !== ""
      ? body.correlation_id.slice(0, MAX_TEXT)
      : headerId;
  return new ApiError({
    status: response.status,
    code: text(body.code, generic.code),
    title: text(body.title, generic.title),
    detail: text(body.detail, generic.detail),
    correlationId: correlation,
    fieldErrors: parseFieldErrors(body.errors),
  });
}

export function networkError(): ApiError {
  return new ApiError({
    status: 0,
    code: "network_error",
    title: "Network error",
    detail: "The service could not be reached.",
  });
}

export function timeoutError(): ApiError {
  return new ApiError({
    status: 0,
    code: "timeout",
    title: "Request timed out",
    detail: "The service took too long to respond.",
  });
}

export function invalidResponseError(status: number): ApiError {
  return new ApiError({
    status,
    code: "invalid_response",
    title: "Invalid response",
    detail: "The service returned an unexpected response.",
  });
}
