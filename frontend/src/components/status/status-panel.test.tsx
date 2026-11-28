import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/errors";

const api = vi.hoisted(() => ({ get: vi.fn(), getResult: vi.fn() }));

vi.mock("@/lib/api/server-client", () => ({ serverApi: api }));
vi.mock("next/server", () => ({ connection: async () => undefined }));

import { StatusPanel, StatusSkeleton } from "./status-panel";

const unreachable = () =>
  new ApiError({ status: 0, code: "network_error", title: "t", detail: "d" });

beforeEach(() => {
  api.get.mockReset();
  api.getResult.mockReset();
});

describe("StatusPanel", () => {
  it("shows a ready backend and disabled AI assistant", async () => {
    api.getResult.mockResolvedValue({
      status: 200,
      ok: true,
      data: { status: "ready" },
    });
    api.get.mockResolvedValue({ ai_assistant: false });
    render(await StatusPanel());
    expect(screen.getByText("Backend ready")).toBeInTheDocument();
    expect(
      screen.getByText("AI assistant: disabled (coming soon)"),
    ).toBeInTheDocument();
  });

  it("shows enabled flags", async () => {
    api.getResult.mockResolvedValue({
      status: 200,
      ok: true,
      data: { status: "ready" },
    });
    api.get.mockResolvedValue({ ai_assistant: true });
    render(await StatusPanel());
    expect(
      screen.getByText("AI assistant: enabled (coming soon)"),
    ).toBeInTheDocument();
  });

  it("shows a backend that is not ready (503)", async () => {
    api.getResult.mockResolvedValue({
      status: 503,
      ok: false,
      data: { status: "not_ready" },
    });
    api.get.mockResolvedValue({ ai_assistant: false });
    render(await StatusPanel());
    expect(screen.getByText("Backend not ready")).toBeInTheDocument();
  });

  it("shows an unreachable backend without details", async () => {
    api.getResult.mockRejectedValue(unreachable());
    api.get.mockRejectedValue(unreachable());
    const { container } = render(await StatusPanel());
    expect(screen.getByText("Backend unreachable")).toBeInTheDocument();
    expect(screen.getByText("AI assistant: unavailable")).toBeInTheDocument();
    expect(container).not.toHaveTextContent(/network_error|ECONN/);
  });
});

describe("StatusSkeleton", () => {
  it("announces loading politely", () => {
    render(<StatusSkeleton />);
    expect(screen.getByRole("status")).toHaveTextContent(
      "Checking system status",
    );
  });
});
