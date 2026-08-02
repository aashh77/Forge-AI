"use client";

import type { AgentName, AgentState } from "@/lib/types";

const LABELS: Record<AgentName, string> = {
  architect: "Architect",
  planner: "Planner",
  backend: "Backend",
  frontend: "Frontend",
  qa: "QA",
  security: "Security",
  reviewer: "Reviewer",
  supervisor: "Supervisor",
  deploy: "Deploy",
};

const ORDER: AgentName[] = ["architect", "planner", "backend", "frontend", "qa", "security", "reviewer", "supervisor", "deploy"];

function statusColor(status: AgentState["status"]): string {
  switch (status) {
    case "success":
      return "bg-emerald-500";
    case "failed":
      return "bg-rose-500";
    case "running":
      return "bg-sky-500 animate-pulse";
    default:
      return "bg-sky-300";
  }
}

function statusLabel(status: AgentState["status"]): string {
  switch (status) {
    case "success":
      return "Running smoothly";
    case "failed":
      return "Issue detected";
    case "running":
      return "Working...";
    case "pending":
      return "Waiting on dependency";
    default:
      return "Idle";
  }
}

export default function AgentBars({
  agents,
  selected,
  onSelect,
}: {
  agents: Record<AgentName, AgentState> | null;
  selected: AgentName | null;
  onSelect: (name: AgentName) => void;
}) {
  return (
    <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-500">Agent Status</h2>
      <div className="flex flex-col gap-3">
        {ORDER.map((name) => {
          const agent = agents?.[name];
          const progress = agent?.progress ?? 0;
          const status = agent?.status ?? "idle";
          const blocks = Math.max(1, Math.round(progress / 10));
          return (
            <button
              key={name}
              onClick={() => onSelect(name)}
              className={`w-full rounded-xl border p-3 text-left transition ${
                selected === name ? "border-slate-900 bg-slate-50" : "border-slate-200 hover:border-slate-400"
              }`}
            >
              <div className="mb-1.5 flex items-center justify-between">
                <span className="text-sm font-semibold text-slate-800">{LABELS[name]}</span>
                <span className="font-mono text-[11px] text-slate-500">{statusLabel(status)}</span>
              </div>
              <div className="mb-1 h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className={`h-full rounded-full transition-all ${statusColor(status)}`}
                  style={{ width: `${Math.max(4, progress)}%` }}
                />
              </div>
              <div className="select-none font-mono text-[11px] leading-none text-slate-400">
                {"█".repeat(blocks)}
                {"░".repeat(10 - blocks)}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
