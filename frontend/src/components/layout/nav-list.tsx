"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

import { NAV_ITEMS } from "./nav-items";

type NavListProps = {
  orientation: "horizontal" | "vertical";
  /** Called after a link is activated (used to close the mobile menu). */
  onNavigate?: () => void;
};

export function NavList({ orientation, onNavigate }: NavListProps) {
  const pathname = usePathname();

  return (
    <ul
      className={cn(
        "flex gap-1",
        orientation === "vertical" ? "flex-col" : "items-center",
      )}
    >
      {NAV_ITEMS.map((item) => (
        <li key={item.label}>
          {item.href ? (
            <Link
              href={item.href}
              onClick={onNavigate}
              aria-current={pathname === item.href ? "page" : undefined}
              className="block rounded-lg px-3 py-2 text-sm font-medium transition-colors hover:bg-muted aria-[current=page]:font-semibold aria-[current=page]:text-primary"
            >
              {item.label}
            </Link>
          ) : (
            <span className="flex cursor-default items-center gap-2 px-3 py-2 text-sm text-muted-foreground">
              {item.label}
              <span className="rounded-full bg-secondary px-2 py-0.5 text-xs text-secondary-foreground">
                Coming soon
              </span>
            </span>
          )}
        </li>
      ))}
    </ul>
  );
}
