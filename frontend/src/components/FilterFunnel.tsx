"use client";

import { useState } from "react";
import type { PipelineResult, Stage } from "@/lib/types";

interface Props {
  result: PipelineResult;
}

export function FilterFunnel({ result }: Props) {
  const [open, setOpen] = useState<string | null>(null);
  const { funnel, stages, traversal } = result;
  const total = funnel.total_nodes;

  const rows: { key: string; label: string; count: number; stage?: Stage; note: string }[] = [
    {
      key: "bfs",
      label: "BFS reachable",
      count: funnel.after_bfs,
      note: `${Object.keys(traversal.reached_levels).length} levels reached · ${traversal.revisits_prevented} revisits prevented`,
    },
    {
      key: "zone2",
      label: "+ Zone 2 injected",
      count: funnel.after_zone2,
      note: `${result.zone2.injected.length} global nodes injected`,
    },
    ...stages.map((s) => ({
      key: s.name,
      label: s.label,
      count: s.count_out,
      stage: s,
      note: `${s.removed} removed · ${s.duration_ms.toFixed(2)} ms`,
    })),
  ];

  return (
    <section className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-5">
      <div className="mb-4 flex items-baseline justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-zinc-400">
          Filter funnel
        </h2>
        <p className="text-xs text-zinc-500">
          {total} nodes in graph → {funnel.candidate_set} in candidate set
        </p>
      </div>

      <div className="space-y-2">
        {rows.map((row) => {
          const pct = total ? (row.count / total) * 100 : 0;
          const isOpen = open === row.key;
          return (
            <div key={row.key}>
              <button
                onClick={() => setOpen(isOpen ? null : row.key)}
                className="group flex w-full items-center gap-3 text-left"
                disabled={!row.stage}
              >
                <span className="w-44 shrink-0 font-mono text-xs text-zinc-400 group-hover:text-zinc-200">
                  {row.label}
                </span>
                <span className="relative h-6 flex-1 overflow-hidden rounded bg-zinc-800/60">
                  <span
                    className="absolute inset-y-0 left-0 rounded bg-gradient-to-r from-emerald-600 to-emerald-400 transition-all duration-500"
                    style={{ width: `${Math.max(pct, 1.5)}%` }}
                  />
                </span>
                <span className="w-10 shrink-0 text-right font-mono text-sm font-semibold text-zinc-100">
                  {row.count}
                </span>
                <span className="hidden w-64 shrink-0 text-right text-[11px] text-zinc-500 lg:block">
                  {row.note}
                </span>
              </button>

              {isOpen && row.stage && (
                <div className="ml-44 mt-2 rounded border border-zinc-800 bg-zinc-950/60 p-3">
                  <code className="block text-[11px] text-emerald-300">{row.stage.sql}</code>
                  {row.stage.excluded.length > 0 ? (
                    <ul className="mt-2 space-y-1">
                      {row.stage.excluded.map((e) => (
                        <li key={e.node_id} className="text-[11px] text-zinc-400">
                          <span className="font-mono text-rose-400">{e.node_id}</span>{" "}
                          <span className="text-zinc-500">{e.title}</span> — {e.reason}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="mt-2 text-[11px] text-zinc-600">nothing excluded at this check</p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <p className="mt-4 text-[11px] text-zinc-600">
        Click a check to see its SQL predicate and the nodes it silently removed.
        Exclusions are never surfaced to the end user — they are audit data.
      </p>
    </section>
  );
}
