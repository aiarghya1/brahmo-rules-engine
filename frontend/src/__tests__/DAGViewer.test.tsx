import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DAGViewer } from "@/components/DAGViewer";
import { MOCK_GRAPH, MOCK_PIPELINE_RESULT } from "./mocks";

describe("DAGViewer", () => {
  it("renders the section heading", () => {
    render(<DAGViewer graph={MOCK_GRAPH} result={MOCK_PIPELINE_RESULT} />);
    expect(screen.getByText("Hierarchy DAG")).toBeInTheDocument();
  });

  it("shows the entry point detail", () => {
    render(<DAGViewer graph={MOCK_GRAPH} result={MOCK_PIPELINE_RESULT} />);
    expect(screen.getByText("Ortho Ward")).toBeInTheDocument();
  });

  it("renders level names from the graph", () => {
    render(<DAGViewer graph={MOCK_GRAPH} result={MOCK_PIPELINE_RESULT} />);
    expect(screen.getByText(/Supra Hospital/)).toBeInTheDocument();
    expect(screen.getByText(/Clinical Division/)).toBeInTheDocument();
    expect(screen.getByText(/Orthopaedics Department/)).toBeInTheDocument();
  });

  it("uses the entry point marker (◉) for the entry level", () => {
    render(<DAGViewer graph={MOCK_GRAPH} result={MOCK_PIPELINE_RESULT} />);
    // Appears in both the tree row and the legend
    expect(screen.getAllByText("◉").length).toBeGreaterThanOrEqual(1);
  });

  it("uses the zone 2 marker (◆) for global constraint levels", () => {
    render(<DAGViewer graph={MOCK_GRAPH} result={MOCK_PIPELINE_RESULT} />);
    // Appears in both the tree row and the legend
    expect(screen.getAllByText("◆").length).toBeGreaterThanOrEqual(1);
  });

  it("shows the legend", () => {
    render(<DAGViewer graph={MOCK_GRAPH} result={MOCK_PIPELINE_RESULT} />);
    expect(screen.getByText("entry point")).toBeInTheDocument();
    expect(screen.getByText("reached by BFS")).toBeInTheDocument();
    expect(screen.getByText("not reachable")).toBeInTheDocument();
    expect(screen.getByText("Zone 2 (injected)")).toBeInTheDocument();
  });
});
