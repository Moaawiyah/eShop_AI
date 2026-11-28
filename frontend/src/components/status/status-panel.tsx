import { connection } from "next/server";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

import {
  loadSystemStatus,
  type ReadinessState,
  type SystemStatus,
} from "./load-status";

const READINESS_LABEL: Record<ReadinessState, string> = {
  ready: "Backend ready",
  not_ready: "Backend not ready",
  unreachable: "Backend unreachable",
};

function aiLabel(enabled: boolean | null): string {
  if (enabled === null) return "AI assistant: unavailable";
  return `AI assistant: ${enabled ? "enabled" : "disabled"} (coming soon)`;
}

function Row({
  term,
  tone,
  children,
}: {
  term: string;
  tone: "good" | "warn";
  children: ReactNode;
}) {
  return (
    <div className="rounded-xl border bg-card p-4">
      <dt className="text-sm text-muted-foreground">{term}</dt>
      <dd
        className={cn(
          "mt-1 font-medium",
          tone === "good" ? "text-foreground" : "text-destructive",
        )}
      >
        {children}
      </dd>
    </div>
  );
}

export function StatusView({ status }: { status: SystemStatus }) {
  return (
    <dl className="grid gap-4 sm:grid-cols-2">
      <Row term="Backend" tone={status.readiness === "ready" ? "good" : "warn"}>
        {READINESS_LABEL[status.readiness]}
      </Row>
      <Row
        term="Feature flags"
        tone={status.aiAssistant === null ? "warn" : "good"}
      >
        {aiLabel(status.aiAssistant)}
      </Row>
    </dl>
  );
}

/** Dynamic: always reflects the backend at request time, never cached. */
export async function StatusPanel() {
  await connection();
  return <StatusView status={await loadSystemStatus()} />;
}

export function StatusSkeleton() {
  return (
    <div role="status" aria-live="polite" className="grid gap-4 sm:grid-cols-2">
      <span className="sr-only">Checking system status</span>
      <div className="h-20 animate-pulse rounded-xl bg-muted motion-reduce:animate-none" />
      <div className="h-20 animate-pulse rounded-xl bg-muted motion-reduce:animate-none" />
    </div>
  );
}
