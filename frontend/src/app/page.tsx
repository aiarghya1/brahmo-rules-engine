"use client";

import { useCallback, useEffect, useState } from "react";
import { CandidateTable } from "@/components/CandidateTable";
import { ComparisonView } from "@/components/ComparisonView";
import { DAGViewer } from "@/components/DAGViewer";
import { FilterFunnel } from "@/components/FilterFunnel";
import { TimingPanel } from "@/components/TimingPanel";
import { UserSelector } from "@/components/UserSelector";
import { api } from "@/lib/api";
import type { GraphPayload, PipelineResult, UserSummary } from "@/lib/types";

export default function Home() {
  const [users, setUsers] = useState<UserSummary[]>([]);
  const [graph, setGraph] = useState<GraphPayload | null>(null);
  const [selected, setSelected] = useState("U-PRIYA");
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [backend, setBackend] = useState<string>("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(async (userId: string) => {
    setRunning(true);
    setError(null);
    try {
      setResult(await api.pipeline(userId));
    } catch (e) {
      setError(String(e));
    } finally {
      setRunning(false);
    }
  }, []);

  useEffect(() => {
    Promise.all([api.users(), api.graph(), api.health()])
      .then(([u, g, h]) => {
        setUsers(u);
        setGraph(g);
        setBackend(`${h.backend} · ${h.nodes} nodes`);
      })
      .catch((e) => setError(String(e)));
  }, []);

  // Switching users re-runs the real pipeline. Nothing here is memoised.
  useEffect(() => {
    void run(selected);
  }, [selected, run]);

  return (
    <main className="mx-auto max-w-[1400px] space-y-5 px-6 py-8">
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-zinc-800 pb-5">
        <div>
          <h1 className="text-xl font-semibold text-zinc-100">
            BRAHMO Rules Engine
            <span className="ml-3 text-sm font-normal text-zinc-500">
              BFS traversal + 5-check filter pipeline
            </span>
          </h1>
          <p className="mt-1 text-xs text-zinc-500">
            Supra Multi-Specialty Hospital · deterministic · zero LLM calls
            {backend && <span className="ml-2 text-zinc-600">· {backend}</span>}
          </p>
        </div>
        <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300 ring-1 ring-emerald-500/30">
          0 LLM calls
        </span>
      </header>

      <UserSelector
        users={users}
        selected={selected}
        onSelect={setSelected}
        onRun={() => void run(selected)}
        running={running}
      />

      {error && (
        <div className="rounded border border-rose-800 bg-rose-950/40 p-4 text-sm text-rose-300">
          {error}
          <p className="mt-1 text-xs text-rose-400/70">
            Is the backend running? <code>uvicorn backend.main:app --reload --port 8000</code>
          </p>
        </div>
      )}

      {result && (
        <>
          <FilterFunnel result={result} />
          <TimingPanel result={result} />

          <div className="grid gap-5 lg:grid-cols-2">
            {graph && <DAGViewer graph={graph} result={result} />}
            <CandidateTable result={result} />
          </div>

          <ComparisonView users={users} />
        </>
      )}
    </main>
  );
}

