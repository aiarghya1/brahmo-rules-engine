import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FilterFunnel } from "@/components/FilterFunnel";
import { MOCK_PIPELINE_RESULT } from "./mocks";

describe("FilterFunnel", () => {
  it("renders the section heading", () => {
    render(<FilterFunnel result={MOCK_PIPELINE_RESULT} />);
    expect(screen.getByText("Filter funnel")).toBeInTheDocument();
  });

  it("shows the funnel summary (total → candidate set)", () => {
    render(<FilterFunnel result={MOCK_PIPELINE_RESULT} />);
    expect(screen.getByText(/50 nodes in graph → 13 in candidate set/)).toBeInTheDocument();
  });

  it("renders BFS and Zone 2 rows", () => {
    render(<FilterFunnel result={MOCK_PIPELINE_RESULT} />);
    expect(screen.getByText("BFS reachable")).toBeInTheDocument();
    expect(screen.getByText("+ Zone 2 injected")).toBeInTheDocument();
  });

  it("renders all five check labels", () => {
    render(<FilterFunnel result={MOCK_PIPELINE_RESULT} />);
    for (const label of ["Check 1 — ISOLATION", "Check 2 — COMPLIANCE", "Check 3 — PERMISSION", "Check 4 — TEMPORAL", "Check 5 — DERIVABILITY"]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it("renders correct counts per stage", () => {
    render(<FilterFunnel result={MOCK_PIPELINE_RESULT} />);
    // BFS: 20, Zone2: 30, then checks: 30, 25, 15, 15, 13
    // Some counts appear multiple times (e.g. 30 appears for zone2 + check1, 15 for check3 + check4)
    const uniqueCounts = [20, 30, 25, 15, 13];
    for (const count of uniqueCounts) {
      expect(screen.getAllByText(String(count)).length).toBeGreaterThanOrEqual(1);
    }
  });

  it("expands a check row on click to show SQL and exclusions", () => {
    render(<FilterFunnel result={MOCK_PIPELINE_RESULT} />);
    // Click on Check 2 — COMPLIANCE (has exclusions)
    fireEvent.click(screen.getByText("Check 2 — COMPLIANCE"));
    // Should show the SQL predicate
    expect(screen.getByText(/compliance_tags/)).toBeInTheDocument();
    // Should show excluded node ids
    expect(screen.getByText("N-O11")).toBeInTheDocument();
    expect(screen.getByText("N-O12")).toBeInTheDocument();
  });

  it("shows 'nothing excluded' for a check with no exclusions", () => {
    render(<FilterFunnel result={MOCK_PIPELINE_RESULT} />);
    fireEvent.click(screen.getByText("Check 1 — ISOLATION"));
    expect(screen.getByText("nothing excluded at this check")).toBeInTheDocument();
  });

  it("collapses when clicking the same check again", () => {
    render(<FilterFunnel result={MOCK_PIPELINE_RESULT} />);
    fireEvent.click(screen.getByText("Check 2 — COMPLIANCE"));
    expect(screen.getByText("N-O11")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Check 2 — COMPLIANCE"));
    expect(screen.queryByText("N-O11")).not.toBeInTheDocument();
  });
});
