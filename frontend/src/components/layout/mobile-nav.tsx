"use client";

import { MenuIcon } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

import { NavList } from "./nav-list";

/** Navigation drawer shown below the `md` breakpoint. */
export function MobileNav() {
  const [open, setOpen] = useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          variant="ghost"
          size="icon-lg"
          className="md:hidden"
          aria-label="Open menu"
        >
          <MenuIcon aria-hidden="true" />
        </Button>
      </SheetTrigger>
      <SheetContent side="left">
        <SheetHeader>
          <SheetTitle>Menu</SheetTitle>
          <SheetDescription className="sr-only">
            Site navigation
          </SheetDescription>
        </SheetHeader>
        <nav aria-label="Mobile" className="px-4">
          <NavList orientation="vertical" onNavigate={() => setOpen(false)} />
        </nav>
      </SheetContent>
    </Sheet>
  );
}
