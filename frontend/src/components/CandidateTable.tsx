"use client";

import { useState } from "react";
import { HINT_STYLES, TYPE_STYLES } from "@/lib/api";
import type { CandidateNode, PipelineResult } from "@/lib/types";

const TYPE_ORDER = ["CONSTRAINT", "DECISION", "ANTI_PATTERN", "FACT"] as const;

export function CandidateTable({ result }: { result: PipelineResult }) {
  const [expanded, setExpanded] = useState<string | null>(null);
  const grouped = TYPE_ORDER.map((type) => ({
    type,
    nodes: result.candidate_set.filter((c) => c.type === type),
  })).filter((g) => g.nodes.length > 0);

  return (
    <section className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-5">
      <div className="mb-4 flex items-baseline justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-zinc-400">
          Candidate set
        </h2>
        <span className="text-xs text-zinc-500">
          {result.candidate_set.length} nodes · ranked by importance, then proximity
        </span>
      </div>

      <div className="space-y-4">
        {grouped.map(({ type, nodes }) => (
          <div key={type}>
            <h3 className="mb-1.5 flex items-center gap-2 text-xs font-semibold">
              <span className={`h-2 w-2 rounded-full ${TYPE_STYLES[type].dot}`} />
              <span className={TYPE_STYLES[type].text}>{type}</span>
              <span className="text-zinc-600">({nodes.length})</span>
            </h3>
            <ul className="space-y-1">
              {nodes.map((node) => (
                <CandidateRow
                  key={node.id}
                  node={node}
                  open={expanded === node.id}
                  onToggle={() => setExpanded(expanded === node.id ? null : node.id)}
                />
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}

function CandidateRow({
  node,
  open,
  onToggle,
}: {
  node: CandidateNode;
  open: boolean;
  onToggle: () => void;
}) {
  return (
    <li className="rounded border border-zinc-800/80 bg-zinc-950/40">
      <button onClick={onToggle} className="flex w-full items-center gap-2 px-3 py-2 text-left">
        <span className="font-mono text-[11px] text-zinc-500">{node.id}</span>
        <span className="flex-1 truncate text-xs text-zinc-200">{node.title}</span>
        {node.reached_via === "ZONE_2_INJECTION" && (
          <span className="rounded bg-violet-500/10 px-1.5 py-0.5 text-[10px] text-violet-300 ring-1 ring-violet-500/30">
            zone 2
          </span>
        )}
        <span className="text-[10px] text-zinc-500">L{node.hierarchy_level}</span>
        <span className="text-[10px] text-zinc-500">d={node.distance_from_entry}</span>
        <span className="text-[10px] text-zinc-400">imp {node.importance.toFixed(2)}</span>
        <span
          className={`rounded px-1.5 py-0.5 text-[10px] ring-1 ${HINT_STYLES[node.compression_hint]}`}
        >
          {node.compression_hint}
        </span>
      </button>
      {open && (
        <p className="border-t border-zinc-800/80 px-3 py-2 text-[11px] leading-relaxed text-zinc-400">
          {node.content}
          <span className="mt-2 block text-[10px] text-zinc-600">
            {node.department ?? "hospital-wide"} · {node.hierarchy_level_id} · zone {node.zone} ·
            reached via {node.reached_via}
          </span>
        </p>
      )}
    </li>
  );
}
