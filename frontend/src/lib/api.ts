import type { ComparePayload, GraphPayload, PipelineResult, UserSummary } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status} ${path}: ${detail}`);
  }
  return (await res.json()) as T;
}

export const api = {
  users: () => get<UserSummary[]>("/api/users"),
  graph: () => get<GraphPayload>("/api/graph"),
  pipeline: (userId: string) => get<PipelineResult>(`/api/pipeline/${userId}`),
  compare: (userIds: string[]) =>
    get<ComparePayload>(`/api/compare?users=${userIds.join(",")}`),
  health: () => get<{ status: string; backend: string; nodes: number }>("/api/health"),
};

export const TYPE_STYLES: Record<string, { dot: string; text: string; chip: string }> = {
  CONSTRAINT: { dot: "bg-rose-500", text: "text-rose-300", chip: "bg-rose-500/10 text-rose-300 ring-rose-500/30" },
  DECISION: { dot: "bg-amber-400", text: "text-amber-300", chip: "bg-amber-400/10 text-amber-300 ring-amber-400/30" },
  ANTI_PATTERN: { dot: "bg-orange-500", text: "text-orange-300", chip: "bg-orange-500/10 text-orange-300 ring-orange-500/30" },
  FACT: { dot: "bg-sky-500", text: "text-sky-300", chip: "bg-sky-500/10 text-sky-300 ring-sky-500/30" },
};

export const HINT_STYLES: Record<string, string> = {
  FULL: "bg-emerald-500/10 text-emerald-300 ring-emerald-500/30",
  COMPRESSED: "bg-yellow-500/10 text-yellow-300 ring-yellow-500/30",
  CONSTRAINT_ONLY: "bg-zinc-500/10 text-zinc-300 ring-zinc-500/30",
};
