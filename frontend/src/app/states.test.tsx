import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import HomePage from "./(storefront)/page";
import ErrorPage from "./error";
import Loading from "./loading";
import NotFound from "./not-found";

vi.mock("next/navigation", () => ({ usePathname: () => "/" }));
vi.mock("next-themes", () => ({
  useTheme: () => ({ theme: "system", setTheme: vi.fn() }),
}));

describe("home page", () => {
  it("shows the intro and a non-interactive category preview", () => {
    render(<HomePage />);

    expect(
      screen.getByRole("heading", { level: 1, name: /electronics/i }),
    ).toBeInTheDocument();
    const list = screen.getByRole("list");
    expect(list.querySelectorAll("a, button")).toHaveLength(0);
    expect(screen.getAllByText("Coming soon")).toHaveLength(6);
  });

  it("does not show prices or cart controls", () => {
    render(<HomePage />);
    expect(screen.queryByText(/\$\d/)).not.toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});

describe("route states", () => {
  it("not-found offers a way back home", () => {
    render(<NotFound />);
    expect(
      screen.getByRole("heading", { name: "Page not found" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to home" })).toHaveAttribute(
      "href",
      "/",
    );
  });

  it("error state offers a retry action", async () => {
    const reset = vi.fn();
    const user = userEvent.setup();
    render(<ErrorPage reset={reset} />);

    expect(screen.getByRole("heading", { name: /went wrong/i })).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(reset).toHaveBeenCalledOnce();
  });

  it("loading state is announced as a status", () => {
    render(<Loading />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading");
  });
});
