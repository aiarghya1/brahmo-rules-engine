import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { UserSelector } from "@/components/UserSelector";
import { MOCK_USERS } from "./mocks";

describe("UserSelector", () => {
  const defaultProps = {
    users: MOCK_USERS,
    selected: "U-PRIYA",
    onSelect: vi.fn(),
    onRun: vi.fn(),
    running: false,
  };

  it("renders the session user label", () => {
    render(<UserSelector {...defaultProps} />);
    expect(screen.getByText("Session user")).toBeInTheDocument();
  });

  it("renders all users in the select dropdown", () => {
    render(<UserSelector {...defaultProps} />);
    const select = screen.getByRole("combobox");
    const options = select.querySelectorAll("option");
    expect(options).toHaveLength(3);
    expect(options[0].textContent).toBe("Nurse Priya — VIEWER, L10, ortho");
  });

  it("calls onSelect when a different user is chosen", () => {
    const onSelect = vi.fn();
    render(<UserSelector {...defaultProps} onSelect={onSelect} />);
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "U-VIKRAM" } });
    expect(onSelect).toHaveBeenCalledWith("U-VIKRAM");
  });

  it("shows Run Pipeline button that calls onRun", () => {
    const onRun = vi.fn();
    render(<UserSelector {...defaultProps} onRun={onRun} />);
    const btn = screen.getByRole("button", { name: "Run Pipeline" });
    fireEvent.click(btn);
    expect(onRun).toHaveBeenCalledOnce();
  });

  it("disables Run button and shows Running… when running", () => {
    render(<UserSelector {...defaultProps} running={true} />);
    const btn = screen.getByRole("button", { name: "Running…" });
    expect(btn).toBeDisabled();
  });

  it("renders role, ceiling, and clearance chips for the selected user", () => {
    render(<UserSelector {...defaultProps} />);
    expect(screen.getByText("VIEWER")).toBeInTheDocument();
    expect(screen.getByText("L10")).toBeInTheDocument();
    // write ceiling and clearance are both "none" for Priya
    expect(screen.getAllByText("none")).toHaveLength(2);
  });

  it("renders clearance values when the user has them", () => {
    render(<UserSelector {...defaultProps} selected="U-VIKRAM" />);
    expect(screen.getByText("MNPI")).toBeInTheDocument();
  });
});
