import type { Metadata } from "next";
import Link from "next/link";

import { SiteShell } from "@/components/layout/site-shell";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = { title: "Page not found" };

export default function NotFound() {
  return (
    <SiteShell>
      <section className="mx-auto max-w-2xl px-4 py-24 text-center sm:px-6">
        <p className="text-sm font-semibold text-primary">404</p>
        <h1 className="mt-2 text-title font-semibold">Page not found</h1>
        <p className="mt-4 text-muted-foreground">
          The page you are looking for does not exist or has moved.
        </p>
        <Button asChild className="mt-8">
          <Link href="/">Back to home</Link>
        </Button>
      </section>
    </SiteShell>
  );
}
