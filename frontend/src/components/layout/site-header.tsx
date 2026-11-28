import Link from "next/link";

import { MobileNav } from "./mobile-nav";
import { NavList } from "./nav-list";
import { ThemeToggle } from "./theme-toggle";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b bg-background/85 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-2 px-4 sm:px-6">
        <MobileNav />
        <Link
          href="/"
          className="rounded-lg px-2 py-1 text-lg font-semibold tracking-tight"
        >
          eShop_AI
        </Link>
        <nav aria-label="Primary" className="ml-4 hidden md:block">
          <NavList orientation="horizontal" />
        </nav>
        <div className="ml-auto">
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
