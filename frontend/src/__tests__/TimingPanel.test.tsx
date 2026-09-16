import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TimingPanel } from "@/components/TimingPanel";
import { MOCK_PIPELINE_RESULT } from "./mocks";

describe("TimingPanel", () => {
  it("renders the section heading", () => {
    render(<TimingPanel result={MOCK_PIPELINE_RESULT} />);
    expect(screen.getByText("Pipeline timing")).toBeInTheDocument();
  });

  it("shows total time and budget", () => {
    render(<TimingPanel result={MOCK_PIPELINE_RESULT} />);
    expect(screen.getByText(/0\.66 ms total · budget 500 ms/)).toBeInTheDocument();
  });

  it("renders all 11 stage timing rows", () => {
    render(<TimingPanel result={MOCK_PIPELINE_RESULT} />);
    for (const label of [
      "permission compile", "entry point", "BFS traversal", "zone 2 inject",
      "check 1 isolation", "check 2 compliance", "check 3 permission",
      "check 4 temporal", "check 5 derivability", "content fetch", "assemble",
    ]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it("renders the LLM calls stat as 0", () => {
    render(<TimingPanel result={MOCK_PIPELINE_RESULT} />);
    expect(screen.getByText("LLM calls")).toBeInTheDocument();
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("renders content rows fetched stat", () => {
    render(<TimingPanel result={MOCK_PIPELINE_RESULT} />);
    expect(screen.getByText("content rows fetched")).toBeInTheDocument();
    // Both candidate_set.length (5) and reached_levels count (5) produce "5"
    expect(screen.getAllByText(String(MOCK_PIPELINE_RESULT.candidate_set.length)).length).toBeGreaterThanOrEqual(1);
  });

  it("renders levels reached and revisits prevented", () => {
    render(<TimingPanel result={MOCK_PIPELINE_RESULT} />);
    expect(screen.getByText("levels reached")).toBeInTheDocument();
    expect(screen.getByText("revisits prevented")).toBeInTheDocument();
  });
});
