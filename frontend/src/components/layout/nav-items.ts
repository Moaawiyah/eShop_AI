export type NavItem = {
  label: string;
  /** Present only for routes that exist today. */
  href?: string;
};

/**
 * Primary navigation. Items without `href` are planned features: they are
 * rendered as non-focusable "coming soon" text, never as links to 404s.
 */
export const NAV_ITEMS: readonly NavItem[] = [
  { label: "Home", href: "/" },
  { label: "Catalog" },
  { label: "AI assistant" },
];
