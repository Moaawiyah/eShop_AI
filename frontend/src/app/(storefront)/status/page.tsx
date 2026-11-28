import type { Metadata } from "next";
import { Suspense } from "react";

import { StatusPanel, StatusSkeleton } from "@/components/status/status-panel";

export const metadata: Metadata = { title: "System status" };

export default function StatusPage() {
  return (
    <section
      aria-labelledby="status-heading"
      className="mx-auto max-w-3xl px-4 py-16 sm:px-6"
    >
      <h1 id="status-heading" className="text-title font-semibold">
        System status
      </h1>
      <p className="mt-3 mb-8 text-muted-foreground">
        Live connectivity between this storefront and its backend.
      </p>
      <Suspense fallback={<StatusSkeleton />}>
        <StatusPanel />
      </Suspense>
    </section>
  );
}
