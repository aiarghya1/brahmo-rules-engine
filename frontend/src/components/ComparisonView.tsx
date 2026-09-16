"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ComparePayload, UserSummary } from "@/lib/types";

export function ComparisonView({ users }: { users: UserSummary[] }) {
  const [selected, setSelected] = useState<string[]>(["U-PRIYA", "U-VIKRAM", "U-SURESH"]);
  const [data, setData] = useState<ComparePayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (selected.length < 2) {
      setData(null);
      return;
    }
    let live = true;
    api
      .compare(selected)
      .then((payload) => live && setData(payload))
      .catch((e) => live && setError(String(e)));
    return () => {
      live = false;
    };
  }, [selected]);

  const toggle = (id: string) => {
    setSelected((current) =>
      current.includes(id)
        ? current.filter((u) => u !== id)
        : current.length >= 4
          ? current
          : [...current, id],
    );
  };

  return (
    <section className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-5">
      <h2 className="mb-1 text-sm font-semibold uppercase tracking-widest text-zinc-400">
        Same graph, different users
      </h2>
      <p className="mb-4 text-xs text-zinc-500">
        Pick 2–4 users. Each column is a full independent pipeline run.
      </p>

      <div className="mb-4 flex flex-wrap gap-2">
        {users.map((u) => (
          <button
            key={u.id}
            onClick={() => toggle(u.id)}
            className={`rounded-full px-3 py-1 text-xs ring-1 transition ${
              selected.includes(u.id)
                ? "bg-emerald-500/15 text-emerald-300 ring-emerald-500/40"
                : "bg-zinc-900 text-zinc-500 ring-zinc-800 hover:text-zinc-300"
            }`}
          >
            {u.name}
          </button>
        ))}
      </div>

      {error && <p className="text-xs text-rose-400">{error}</p>}

      {data && (
        <>
          <div className="grid gap-3" style={{ gridTemplateColumns: `repeat(${data.results.length}, minmax(0, 1fr))` }}>
            {data.results.map((r) => (
              <div key={r.user} className="rounded border border-zinc-800 bg-zinc-950/50 p-3">
                <div className="text-sm font-semibold text-zinc-100">{r.user_name}</div>
                <div className="text-[11px] text-zinc-500">
                  {r.role} · L{r.ceiling_level} · {r.department}
                </div>
                <div className="mt-3 font-mono text-3xl text-emerald-300">
                  {r.funnel.candidate_set}
                </div>
                <div className="text-[11px] text-zinc-600">of {r.funnel.total_nodes} nodes</div>

                <dl className="mt-3 space-y-0.5 text-[11px]">
                  <Row k="entry" v={r.entry_point} />
                  <Row k="BFS reach" v={String(r.funnel.after_bfs)} />
                  <Row k="after checks" v={String(r.funnel.after_check5)} />
                  <Row k="time" v={`${r.pipeline_timing.total_ms.toFixed(2)} ms`} />
                </dl>

                <div className="mt-3 border-t border-zinc-800 pt-2">
                  <div className="text-[10px] uppercase tracking-wider text-zinc-600">
                    only this user ({data.exclusive_node_ids[r.user]?.length ?? 0})
                  </div>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {(data.exclusive_node_ids[r.user] ?? []).slice(0, 14).map((id) => (
                      <span key={id} className="rounded bg-amber-500/10 px-1 font-mono text-[10px] text-amber-300">
                        {id}
                      </span>
                    ))}
                    {(data.exclusive_node_ids[r.user] ?? []).length === 0 && (
                      <span className="text-[10px] text-zinc-600">none — subset of the others</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-3 rounded border border-zinc-800 bg-zinc-950/50 p-3">
            <div className="text-[10px] uppercase tracking-wider text-zinc-600">
              shared by all selected ({data.shared_node_ids.length})
            </div>
            <div className="mt-1 flex flex-wrap gap-1">
              {data.shared_node_ids.map((id) => (
                <span key={id} className="rounded bg-zinc-800 px-1 font-mono text-[10px] text-zinc-400">
                  {id}
                </span>
              ))}
            </div>
          </div>
        </>
      )}
    </section>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between gap-2">
      <dt className="text-zinc-600">{k}</dt>
      <dd className="truncate font-mono text-zinc-300">{v}</dd>
    </div>
  );
}
