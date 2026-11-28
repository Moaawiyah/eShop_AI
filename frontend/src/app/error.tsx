"use client";

import { SiteShell } from "@/components/layout/site-shell";
import { Button } from "@/components/ui/button";

/** Route error boundary. Deliberately shows no error details to the visitor. */
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <SiteShell>
      <section className="mx-auto max-w-2xl px-4 py-24 text-center sm:px-6">
        <h1 className="text-title font-semibold">Something went wrong</h1>
        <p className="mt-4 text-muted-foreground">
          We could not load this page. Please try again.
        </p>
        <Button className="mt-8" onClick={reset}>
          Try again
        </Button>
      </section>
    </SiteShell>
  );
}
