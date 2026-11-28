import type { paths } from "./schema";

export type ApiPath = keyof paths;

/** Paths that define a GET operation, derived from the generated schema. */
export type PathsWithGet = {
  [P in ApiPath]: paths[P] extends { get: object } ? P : never;
}[ApiPath];

type GetOperation<P extends PathsWithGet> = paths[P] extends { get: infer Op }
  ? Op
  : never;

type Responses<P extends PathsWithGet> =
  GetOperation<P> extends { responses: infer R } ? R : never;

type JsonBody<R> = R extends { content: { "application/json": infer B } }
  ? B
  : never;

/** Statuses (with a JSON body) documented for a GET operation. */
export type DocumentedStatus<P extends PathsWithGet> = {
  [S in keyof Responses<P>]: S extends number
    ? Responses<P>[S] extends { content: { "application/json": unknown } }
      ? S
      : never
    : never;
}[keyof Responses<P>];

/** JSON body of the 200 response. */
export type GetResponse<P extends PathsWithGet> = JsonBody<
  Responses<P> extends { 200: infer R } ? R : never
>;

/** A response with a documented status and its typed body. */
export type ApiResult<P extends PathsWithGet, S extends DocumentedStatus<P>> = {
  [K in S]: {
    status: K;
    ok: K extends 200 ? true : false;
    data: JsonBody<K extends keyof Responses<P> ? Responses<P>[K] : never>;
  };
}[S];

export type CsrfTokenProvider = () => string | null | undefined;

export type RequestOptions = {
  signal?: AbortSignal;
  /** Overrides the client's default timeout (milliseconds). */
  timeoutMs?: number;
};
