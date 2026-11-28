import { Button } from "@/components/ui/button";

export function HeroSection() {
  return (
    <section
      aria-labelledby="hero-heading"
      className="bg-gradient-to-b from-accent/60 to-background"
    >
      <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-28">
        <p className="mb-4 text-sm font-semibold tracking-wide text-primary uppercase">
          Portfolio demo
        </p>
        <h1
          id="hero-heading"
          className="max-w-3xl text-display font-semibold text-balance"
        >
          Electronics, chosen with clarity.
        </h1>
        <p className="mt-6 max-w-2xl text-lg text-pretty text-muted-foreground">
          eShop_AI is an educational, cloud-native storefront with an AI
          shopping assistant. The catalog, search and checkout are being built
          step by step and are not available yet.
        </p>
        <div className="mt-8">
          <Button asChild size="lg" className="h-11 px-5 text-base">
            <a href="#categories">Preview the categories</a>
          </Button>
        </div>
      </div>
    </section>
  );
}
