import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { MobileNav } from "./mobile-nav";

vi.mock("next/navigation", () => ({ usePathname: () => "/" }));

describe("MobileNav", () => {
  it("is closed until the menu button is activated", () => {
    render(<MobileNav />);
    expect(
      screen.getByRole("button", { name: "Open menu" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("opens a labelled dialog with navigation", async () => {
    const user = userEvent.setup();
    render(<MobileNav />);
    await user.click(screen.getByRole("button", { name: "Open menu" }));

    const dialog = await screen.findByRole("dialog", { name: "Menu" });
    const nav = within(dialog).getByRole("navigation", { name: "Mobile" });
    expect(within(nav).getByRole("link", { name: "Home" })).toHaveAttribute(
      "href",
      "/",
    );
  });

  it("renders planned routes as text, not links", async () => {
    const user = userEvent.setup();
    render(<MobileNav />);
    await user.click(screen.getByRole("button", { name: "Open menu" }));

    const nav = await screen.findByRole("navigation", { name: "Mobile" });
    expect(
      within(nav)
        .getAllByRole("link")
        .map((link) => link.textContent),
    ).toEqual(["Home", "System status"]);
    expect(within(nav).getByText("Catalog")).toBeInTheDocument();
    expect(within(nav).getAllByText("Coming soon")).toHaveLength(2);
  });

  it("closes with Escape", async () => {
    const user = userEvent.setup();
    render(<MobileNav />);
    await user.click(screen.getByRole("button", { name: "Open menu" }));
    await screen.findByRole("dialog");
    await user.keyboard("{Escape}");

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("closes after a link is activated", async () => {
    const user = userEvent.setup();
    render(<MobileNav />);
    await user.click(screen.getByRole("button", { name: "Open menu" }));
    await user.click(await screen.findByRole("link", { name: "Home" }));

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
