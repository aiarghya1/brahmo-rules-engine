"use client";

import type { PipelineResult } from "@/lib/types";

const STAGE_ORDER: [string, string][] = [
  ["permission_compile_ms", "permission compile"],
  ["entry_point_ms", "entry point"],
  ["bfs_ms", "BFS traversal"],
  ["zone2_inject_ms", "zone 2 inject"],
  ["check1_isolation_ms", "check 1 isolation"],
  ["check2_compliance_ms", "check 2 compliance"],
  ["check3_permission_ms", "check 3 permission"],
  ["check4_temporal_ms", "check 4 temporal"],
  ["check5_derivability_ms", "check 5 derivability"],
  ["content_fetch_ms", "content fetch"],
  ["assemble_ms", "assemble"],
];

export function TimingPanel({ result }: { result: PipelineResult }) {
  const timing = result.pipeline_timing;
  const total = timing.total_ms ?? 0;
  const max = Math.max(...STAGE_ORDER.map(([k]) => timing[k] ?? 0), 0.0001);

  return (
    <section className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-5">
      <div className="mb-3 flex items-baseline justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-zinc-400">
          Pipeline timing
        </h2>
        <span className="font-mono text-xs text-emerald-300">
          {total.toFixed(2)} ms total · budget 500 ms
        </span>
      </div>

      <div className="space-y-1">
        {STAGE_ORDER.map(([key, label]) => {
          const ms = timing[key] ?? 0;
          return (
            <div key={key} className="flex items-center gap-2 text-[11px]">
              <span className="w-40 shrink-0 text-zinc-500">{label}</span>
              <span className="relative h-1.5 flex-1 overflow-hidden rounded bg-zinc-800">
                <span
                  className="absolute inset-y-0 left-0 rounded bg-sky-500/70"
                  style={{ width: `${Math.max((ms / max) * 100, 1)}%` }}
                />
              </span>
              <span className="w-16 shrink-0 text-right font-mono text-zinc-400">
                {ms.toFixed(3)}
              </span>
            </div>
          );
        })}
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 border-t border-zinc-800 pt-3 text-[11px] sm:grid-cols-4">
        <Stat label="LLM calls" value={String(result.llm_calls)} accent />
        <Stat label="content rows fetched" value={String(result.candidate_set.length)} />
        <Stat label="levels reached" value={String(Object.keys(result.traversal.reached_levels).length)} />
        <Stat label="revisits prevented" value={String(result.traversal.revisits_prevented)} />
      </div>
    </section>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div>
      <div className={`font-mono text-lg ${accent ? "text-emerald-300" : "text-zinc-200"}`}>
        {value}
      </div>
      <div className="text-zinc-600">{label}</div>
    </div>
  );
}
