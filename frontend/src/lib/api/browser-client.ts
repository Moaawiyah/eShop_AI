import { createApiClient } from "./client";

/**
 * Client for the browser: same-origin relative URLs, so `/api/v1/*` goes
 * through the Next.js proxy route. The CSRF token provider is wired with
 * authentication (SHOP-032); until then unsafe requests send no token.
 */
export const browserApi = createApiClient({
  baseUrl: "",
  credentials: "same-origin",
});
