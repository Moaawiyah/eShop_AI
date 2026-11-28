import "server-only";

import { getServerConfig } from "@/lib/config/server";

import { createApiClient } from "./client";

/**
 * Client for server components: calls the backend's internal URL (read at
 * request time). Public endpoints only: the incoming session cookie is not
 * forwarded yet (authenticated forwarding arrives with auth, SHOP-032).
 */
export const serverApi = createApiClient({
  baseUrl: () => getServerConfig().backendInternalUrl,
});
