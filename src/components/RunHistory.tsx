"use client";

import { useState } from "react";
import { DEMO_RUN_ID } from "@/lib/constants";
import type { RunSummary } from "@/lib/types";

export default function RunHistory({
  runs,
  activeRunId,
  onSelect,
  onRename,
  onDelete,
  renamingId,
  deletingId,
}: {
  runs: RunSummary[];
  activeRunId: string | null;
  onSelect: (id: string) => void;
  onRename: (id: string, name: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  renamingId: string | null;
  deletingId: string | null;
}) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");

  const startEdit = (run: RunSummary) => {
    setEditingId(run.id);
    setEditName(run.name);
  };

  const submitEdit = async (id: string) => {
    const trimmed = editName.trim();
    if (!trimmed) return;
    await onRename(id, trimmed);
    setEditingId(null);
  };

  return (
    <div className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
      <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
        Project History
      </h2>
      <div className="flex max-h-[26rem] flex-col gap-2 overflow-y-auto">
        {runs.length === 0 && (
          <p className="text-sm text-slate-400">No projects yet. Forge one to get started.</p>
        )}
        {runs.map((r) => {
          const isDemo = r.id === DEMO_RUN_ID;
          return (
            <div
              key={r.id}
              className={`rounded-xl border p-3 transition ${
                activeRunId === r.id
                  ? "border-slate-900 bg-slate-900 text-white"
                  : "border-slate-200 bg-white"
              }`}
            >
              {editingId === r.id ? (
                <div className="flex items-center gap-2">
                  <input
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && submitEdit(r.id)}
                    className="flex-1 rounded border border-slate-300 px-2 py-1 text-sm text-slate-900"
                    autoFocus
                  />
                  <button
                    onClick={() => submitEdit(r.id)}
                    disabled={renamingId === r.id}
                    className="text-xs font-medium text-slate-600 hover:text-slate-900"
                  >
                    {renamingId === r.id ? "Saving..." : "Save"}
                  </button>
                  <button
                    onClick={() => setEditingId(null)}
                    className="text-xs font-medium text-slate-500 hover:text-slate-800"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => onSelect(r.id)}
                  className="w-full text-left"
                >
                  <p
                    className={`line-clamp-2 text-sm font-semibold ${
                      activeRunId === r.id ? "text-white" : "text-slate-800"
                    }`}
                  >
                    {isDemo && <span className="mr-1.5" aria-label="Pinned demo project" title="Pinned demo project">📌</span>}
                    {r.name}
                  </p>
                  <p
                    className={`mt-1 text-xs ${
                      activeRunId === r.id ? "text-slate-300" : "text-slate-500"
                    }`}
                  >
                    {r.status} · {new Date(r.created_at * 1000).toLocaleString()}
                  </p>
                </button>
              )}
              {editingId !== r.id && !isDemo && (
                <div className="mt-2 flex gap-2">
                  <button
                    onClick={() => startEdit(r)}
                    className={`text-xs font-medium ${
                      activeRunId === r.id ? "text-slate-300 hover:text-white" : "text-slate-500 hover:text-slate-800"
                    }`}
                  >
                    Rename
                  </button>
                  <button
                    onClick={() => onDelete(r.id)}
                    disabled={deletingId === r.id}
                    className={`text-xs font-medium ${
                      activeRunId === r.id ? "text-rose-300 hover:text-rose-200" : "text-rose-500 hover:text-rose-700"
                    }`}
                  >
                    {deletingId === r.id ? "Deleting..." : "Delete"}
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
