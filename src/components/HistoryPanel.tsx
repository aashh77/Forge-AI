"use client";

import type { Checkpoint, Debate } from "@/lib/types";

export default function HistoryPanel({
  checkpoints,
  debates,
  onRollback,
  rollingBack,
}: {
  checkpoints: Checkpoint[];
  debates: Debate[];
  onRollback: (checkpointId: string) => void;
  rollingBack: string | null;
}) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Checkpoints (self-healing rollback)
        </h2>
        <div className="flex max-h-72 flex-col gap-2 overflow-y-auto">
          {checkpoints.length === 0 && <p className="text-sm text-slate-400">No checkpoints yet.</p>}
          {[...checkpoints].reverse().map((cp) => (
            <div key={cp.id} className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 p-3 text-sm">
              <div className="min-w-0">
                <p className="break-words font-medium text-slate-800">
                  Checkpoint #{cp.number} — {cp.tag || "milestone"}
                </p>
                <p className="break-words text-xs text-slate-500">{cp.description}</p>
              </div>
              <button
                onClick={() => onRollback(cp.id)}
                disabled={rollingBack === cp.id}
                className="shrink-0 rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-50"
              >
                {rollingBack === cp.id ? "Rolling back..." : "Rollback"}
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Supervisor Debates
        </h2>
        <div className="flex max-h-72 flex-col gap-3 overflow-y-auto">
          {debates.length === 0 && (
            <p className="text-sm text-slate-400">No conflicts detected between agents (yet).</p>
          )}
          {debates.map((d, i) => (
            <details key={i} className="rounded-lg border border-slate-200 p-3 text-sm">
              <summary className="cursor-pointer break-words font-medium text-slate-800">
                Conflict: {d.topic} — Winner: {d.verdict?.winner}
              </summary>
              <div className="mt-2 flex flex-col gap-2">
                {d.transcript.map((t, j) => (
                  <p key={j} className="break-words text-xs text-slate-600">
                    <span className="font-semibold text-slate-800">
                      [{t.agent} round {t.round}]
                    </span>{" "}
                    {t.argument}
                  </p>
                ))}
                <p className="mt-1 text-xs text-slate-700">
                  <span className="font-semibold">Verdict:</span> {d.verdict?.justification} (
                  {d.verdict?.confidence}% confidence)
                </p>
              </div>
            </details>
          ))}
        </div>
      </div>
    </div>
  );
}
