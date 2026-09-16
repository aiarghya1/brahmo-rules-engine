"use client";

import type { GraphPayload, PipelineResult } from "@/lib/types";

interface Props {
  graph: GraphPayload;
  result: PipelineResult;
}

/**
 * Renders the hierarchy DAG as an indented tree (following each level's first
 * parent) and marks every level with what the traversal did to it.
 */
export function DAGViewer({ graph, result }: Props) {
  const reached = result.traversal.reached_levels;
  const candidateIds = new Set(result.candidate_set.map((c) => c.id));

  const nodesByLevel = new Map<string, number>();
  const survivorsByLevel = new Map<string, number>();
  for (const node of graph.nodes) {
    nodesByLevel.set(node.hierarchy_level_id, (nodesByLevel.get(node.hierarchy_level_id) ?? 0) + 1);
    if (candidateIds.has(node.id)) {
      survivorsByLevel.set(
        node.hierarchy_level_id,
        (survivorsByLevel.get(node.hierarchy_level_id) ?? 0) + 1,
      );
    }
  }

  const childrenOf = new Map<string, string[]>();
  const roots: string[] = [];
  for (const level of graph.levels) {
    if (level.parent_ids.length === 0) roots.push(level.id);
    else {
      const primary = level.parent_ids[0];
      childrenOf.set(primary, [...(childrenOf.get(primary) ?? []), level.id]);
    }
  }
  const byId = new Map(graph.levels.map((l) => [l.id, l]));

  const rows: { id: string; depth: number }[] = [];
  const walk = (id: string, depth: number) => {
    rows.push({ id, depth });
    for (const child of childrenOf.get(id) ?? []) walk(child, depth + 1);
  };
  roots.forEach((r) => walk(r, 0));

  return (
    <section className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-5">
      <h2 className="mb-1 text-sm font-semibold uppercase tracking-widest text-zinc-400">
        Hierarchy DAG
      </h2>
      <p className="mb-4 text-xs text-zinc-500">
        Entry: <span className="text-emerald-300">{result.entry_point_detail.level_name}</span> (L
        {result.entry_point_detail.level_number}) — {result.entry_point_detail.reason}
      </p>

      <div className="space-y-0.5 font-mono text-xs">
        {rows.map(({ id, depth }) => {
          const level = byId.get(id)!;
          const distance = reached[id];
          const isReached = distance !== undefined;
          const isEntry = id === result.entry_point;
          const isZone2 = level.zone === 2;
          const total = nodesByLevel.get(id) ?? 0;
          const kept = survivorsByLevel.get(id) ?? 0;
          const multiParent = level.parent_ids.length > 1;

          const marker = isEntry ? "◉" : isZone2 ? "◆" : isReached ? "●" : "○";
          const colour = isEntry
            ? "text-emerald-300"
            : isZone2
              ? "text-violet-300"
              : isReached
                ? "text-zinc-200"
                : "text-zinc-700";

          return (
            <div
              key={id}
              className={`flex items-center gap-2 rounded px-2 py-1 ${
                isEntry ? "bg-emerald-500/10" : isReached ? "bg-zinc-800/30" : ""
              }`}
              style={{ paddingLeft: `${depth * 16 + 8}px` }}
            >
              <span className={colour}>{marker}</span>
              <span className={`${colour} ${isEntry ? "font-bold" : ""}`}>
                [L{level.level_number}] {level.level_name}
              </span>
              {multiParent && (
                <span className="rounded bg-violet-500/10 px-1.5 text-[10px] text-violet-300 ring-1 ring-violet-500/30">
                  multi-parent → {level.parent_ids.join(" + ")}
                </span>
              )}
              {isReached && (
                <span className="text-[10px] text-zinc-500">d={distance}</span>
              )}
              {total > 0 && (
                <span
                  className={`ml-auto text-[10px] ${kept > 0 ? "text-emerald-400" : "text-zinc-600"}`}
                >
                  {kept}/{total} nodes kept
                </span>
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-4 flex flex-wrap gap-4 border-t border-zinc-800 pt-3 text-[11px] text-zinc-500">
        <span><span className="text-emerald-300">◉</span> entry point</span>
        <span><span className="text-zinc-200">●</span> reached by BFS</span>
        <span><span className="text-zinc-700">○</span> not reachable</span>
        <span><span className="text-violet-300">◆</span> Zone 2 (injected)</span>
      </div>
    </section>
  );
}
