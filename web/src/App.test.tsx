import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("Multi-Model Debate GUI", () => {
  it("shows the full panel with optional Critic B", async () => {
    render(<App />);

    expect(await screen.findByText("Multi-Model Debate")).toBeInTheDocument();
    expect(screen.getByText("Builder")).toBeInTheDocument();
    expect(screen.getByText("Critic A")).toBeInTheDocument();
    expect(screen.getByText("Critic B")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Judge" })).toBeInTheDocument();
    expect(screen.getByText("Optional")).toBeInTheDocument();
  });

  it("starts a hosted demo run without user keys", async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: /start debate/i }));

    await waitFor(() => {
      expect(screen.getByText(/Final report/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/No keys needed/i)).toBeInTheDocument();
  });

  it("lets the same ChatGPT account fill multiple fresh seats", async () => {
    render(<App />);

    expect(await screen.findAllByDisplayValue("GPT-5 Thinking")).toHaveLength(3);
    expect(screen.getAllByText("Fresh instance")).toHaveLength(4);
  });
});
