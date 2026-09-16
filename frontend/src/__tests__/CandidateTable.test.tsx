import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CandidateTable } from "@/components/CandidateTable";
import { MOCK_PIPELINE_RESULT } from "./mocks";

describe("CandidateTable", () => {
  it("renders the section heading", () => {
    render(<CandidateTable result={MOCK_PIPELINE_RESULT} />);
    expect(screen.getByText("Candidate set")).toBeInTheDocument();
  });

  it("shows the total count and ranking description", () => {
    render(<CandidateTable result={MOCK_PIPELINE_RESULT} />);
    expect(screen.getByText(/5 nodes · ranked by importance, then proximity/)).toBeInTheDocument();
  });

  it("groups candidates by type", () => {
    render(<CandidateTable result={MOCK_PIPELINE_RESULT} />);
    expect(screen.getByText("CONSTRAINT")).toBeInTheDocument();
    expect(screen.getByText("DECISION")).toBeInTheDocument();
    expect(screen.getByText("ANTI_PATTERN")).toBeInTheDocument();
    expect(screen.getByText("FACT")).toBeInTheDocument();
  });

  it("shows type group counts", () => {
    render(<CandidateTable result={MOCK_PIPELINE_RESULT} />);
    // CONSTRAINT has 2 nodes, DECISION 1, ANTI_PATTERN 1, FACT 1
    expect(screen.getByText("(2)")).toBeInTheDocument();
  });

  it("renders candidate titles", () => {
    render(<CandidateTable result={MOCK_PIPELINE_RESULT} />);
    expect(screen.getByText("Patient Rajan: Absolute NSAID Contraindication")).toBeInTheDocument();
    expect(screen.getByText("Warfarin-NSAID Interaction")).toBeInTheDocument();
  });

  it("renders node ids", () => {
    render(<CandidateTable result={MOCK_PIPELINE_RESULT} />);
    expect(screen.getByText("N-O14")).toBeInTheDocument();
    expect(screen.getByText("N-G01")).toBeInTheDocument();
  });

  it("shows zone 2 badge for injected nodes", () => {
    render(<CandidateTable result={MOCK_PIPELINE_RESULT} />);
    const zone2Badges = screen.getAllByText("zone 2");
    expect(zone2Badges.length).toBeGreaterThan(0);
  });

  it("shows compression hints", () => {
    render(<CandidateTable result={MOCK_PIPELINE_RESULT} />);
    const fullHints = screen.getAllByText("FULL");
    const constraintHints = screen.getAllByText("CONSTRAINT_ONLY");
    expect(fullHints.length).toBeGreaterThan(0);
    expect(constraintHints.length).toBeGreaterThan(0);
  });

  it("expands a candidate row on click to show content", () => {
    render(<CandidateTable result={MOCK_PIPELINE_RESULT} />);
    fireEvent.click(screen.getByText("Patient Rajan: Absolute NSAID Contraindication"));
    expect(screen.getByText(/Patient Rajan has documented allergy/)).toBeInTheDocument();
  });

  it("collapses when clicking the same candidate again", () => {
    render(<CandidateTable result={MOCK_PIPELINE_RESULT} />);
    fireEvent.click(screen.getByText("Patient Rajan: Absolute NSAID Contraindication"));
    expect(screen.getByText(/Patient Rajan has documented allergy/)).toBeInTheDocument();
    fireEvent.click(screen.getByText("Patient Rajan: Absolute NSAID Contraindication"));
    expect(screen.queryByText(/Patient Rajan has documented allergy/)).not.toBeInTheDocument();
  });
});
