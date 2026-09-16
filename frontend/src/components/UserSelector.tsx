"use client";

import type { UserSummary } from "@/lib/types";

interface Props {
  users: UserSummary[];
  selected: string;
  onSelect: (id: string) => void;
  onRun: () => void;
  running: boolean;
}

export function UserSelector({ users, selected, onSelect, onRun, running }: Props) {
  const user = users.find((u) => u.id === selected);

  return (
    <div className="flex flex-wrap items-end gap-4">
      <label className="flex flex-col gap-1.5">
        <span className="text-xs uppercase tracking-widest text-zinc-500">Session user</span>
        <select
          value={selected}
          onChange={(e) => onSelect(e.target.value)}
          className="min-w-[22rem] rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-emerald-500"
        >
          {users.map((u) => (
            <option key={u.id} value={u.id}>
              {u.label}
            </option>
          ))}
        </select>
      </label>

      <button
        onClick={onRun}
        disabled={running}
        className="rounded-md bg-emerald-500 px-5 py-2 text-sm font-semibold text-zinc-950 transition hover:bg-emerald-400 disabled:opacity-50"
      >
        {running ? "Running…" : "Run Pipeline"}
      </button>

      {user && (
        <div className="flex flex-wrap gap-2 text-xs">
          <Chip label="role" value={user.role} />
          <Chip label="read ceiling" value={`L${user.ceiling_level}`} />
          <Chip label="write ceiling" value={user.write_ceiling ? `L${user.write_ceiling}` : "none"} />
          <Chip
            label="clearance"
            value={user.compliance_clearance.length ? user.compliance_clearance.join(", ") : "none"}
          />
        </div>
      )}
    </div>
  );
}

function Chip({ label, value }: { label: string; value: string }) {
  return (
    <span className="rounded border border-zinc-800 bg-zinc-900/60 px-2 py-1 text-zinc-400">
      <span className="text-zinc-600">{label}</span>{" "}
      <span className="font-medium text-zinc-200">{value}</span>
    </span>
  );
}
