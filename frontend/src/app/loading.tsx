import { SiteShell } from "@/components/layout/site-shell";

export default function Loading() {
  return (
    <SiteShell>
      <div
        role="status"
        aria-live="polite"
        className="mx-auto max-w-6xl space-y-4 px-4 py-20 sm:px-6"
      >
        <span className="sr-only">Loading</span>
        <div className="h-10 w-2/3 animate-pulse rounded-xl bg-muted motion-reduce:animate-none" />
        <div className="h-5 w-1/2 animate-pulse rounded-xl bg-muted motion-reduce:animate-none" />
        <div className="h-5 w-1/3 animate-pulse rounded-xl bg-muted motion-reduce:animate-none" />
      </div>
    </SiteShell>
  );
}
