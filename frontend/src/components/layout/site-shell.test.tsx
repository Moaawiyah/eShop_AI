import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { NavList } from "./nav-list";
import { SiteShell } from "./site-shell";

let pathname = "/";
vi.mock("next/navigation", () => ({ usePathname: () => pathname }));
vi.mock("next-themes", () => ({
  useTheme: () => ({ theme: "system", setTheme: vi.fn() }),
}));

describe("SiteShell landmarks", () => {
  it("renders header, labelled nav, main and footer", () => {
    render(
      <SiteShell>
        <h1>Page</h1>
      </SiteShell>,
    );

    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(
      screen.getByRole("navigation", { name: "Primary" }),
    ).toBeInTheDocument();
    const main = screen.getByRole("main");
    expect(main).toHaveAttribute("id", "main-content");
    expect(within(main).getByRole("heading", { name: "Page" })).toBeVisible();
    expect(screen.getByRole("contentinfo")).toBeInTheDocument();
  });

  it("states that payments are simulated in the footer", () => {
    render(<SiteShell>content</SiteShell>);
    expect(
      within(screen.getByRole("contentinfo")).getByText(
        "Portfolio demo — all payments are simulated; no real orders are placed.",
      ),
    ).toBeInTheDocument();
  });

  it("makes the skip link the first tab stop and targets main", async () => {
    const user = userEvent.setup();
    render(<SiteShell>content</SiteShell>);
    await user.tab();

    const skip = screen.getByRole("link", { name: "Skip to main content" });
    expect(skip).toHaveFocus();
    expect(skip).toHaveAttribute("href", "#main-content");
    expect(screen.getByRole("main")).toHaveAttribute("id", "main-content");
  });
});

describe("NavList", () => {
  it("marks the current page and exposes only real routes as links", () => {
    pathname = "/";
    render(<NavList orientation="horizontal" />);

    const links = screen.getAllByRole("link");
    expect(links.map((link) => link.textContent)).toEqual([
      "Home",
      "System status",
    ]);
    expect(links[0]).toHaveAttribute("aria-current", "page");
    expect(links[1]).not.toHaveAttribute("aria-current");
    expect(links[1]).toHaveAttribute("href", "/status");
    expect(screen.getByText("AI assistant")).toBeInTheDocument();
  });

  it("does not mark Home as current on other paths", () => {
    pathname = "/elsewhere";
    render(<NavList orientation="vertical" />);
    expect(screen.getByRole("link", { name: "Home" })).not.toHaveAttribute(
      "aria-current",
    );
  });
});
