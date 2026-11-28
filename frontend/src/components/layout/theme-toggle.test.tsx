import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ThemeToggle } from "./theme-toggle";

const setTheme = vi.fn();
let currentTheme: string | undefined = "light";

vi.mock("next-themes", () => ({
  useTheme: () => ({ theme: currentTheme, setTheme }),
}));

describe("ThemeToggle", () => {
  beforeEach(() => {
    setTheme.mockClear();
    currentTheme = "light";
  });

  it("exposes an accessible name and is collapsed initially", () => {
    render(<ThemeToggle />);
    const trigger = screen.getByRole("button", { name: "Change theme" });
    expect(trigger).toHaveAttribute("aria-expanded", "false");
  });

  it("opens with the keyboard and lists light, dark and system", async () => {
    const user = userEvent.setup();
    render(<ThemeToggle />);
    await user.tab();
    await user.keyboard("{Enter}");

    const options = await screen.findAllByRole("menuitemradio");
    expect(options.map((o) => o.textContent)).toEqual([
      "Light",
      "Dark",
      "System",
    ]);
    expect(screen.getByRole("menuitemradio", { name: "Light" })).toBeChecked();
  });

  it("selects a theme from the menu", async () => {
    const user = userEvent.setup();
    render(<ThemeToggle />);
    await user.click(screen.getByRole("button", { name: "Change theme" }));
    await user.click(
      await screen.findByRole("menuitemradio", { name: "Dark" }),
    );

    expect(setTheme).toHaveBeenCalledWith("dark");
  });

  it("falls back to System before the theme is known", async () => {
    currentTheme = undefined;
    const user = userEvent.setup();
    render(<ThemeToggle />);
    await user.click(screen.getByRole("button", { name: "Change theme" }));

    expect(
      await screen.findByRole("menuitemradio", { name: "System" }),
    ).toBeChecked();
  });
});
