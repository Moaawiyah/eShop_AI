import { serverApi } from "@/lib/api/server-client";

export type ReadinessState = "ready" | "not_ready" | "unreachable";

export type SystemStatus = {
  readiness: ReadinessState;
  /** `null` when the flags could not be loaded. */
  aiAssistant: boolean | null;
};

/** Never throws and never exposes error details: failures become states. */
export async function loadSystemStatus(): Promise<SystemStatus> {
  const [readiness, flags] = await Promise.allSettled([
    serverApi.getResult("/health/ready", [200, 503]),
    serverApi.get("/api/v1/config/public-flags"),
  ]);
  return {
    readiness:
      readiness.status === "fulfilled"
        ? readiness.value.data.status
        : "unreachable",
    aiAssistant: flags.status === "fulfilled" ? flags.value.ai_assistant : null,
  };
}
