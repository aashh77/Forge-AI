"use client";

import type { DeploymentInfo, RunState } from "@/lib/types";

const STATUS_LABEL: Record<string, string> = {
  not_started: "Not started",
  installing: "Installing dependencies...",
  starting: "Starting server...",
  running: "Live",
  not_live: "Not live",
  failed: "Failed",
};

const STATUS_COLOR: Record<string, string> = {
  not_started: "bg-slate-100 text-slate-600",
  installing: "bg-sky-100 text-sky-700",
  starting: "bg-sky-100 text-sky-700",
  running: "bg-emerald-100 text-emerald-700",
  not_live: "bg-amber-100 text-amber-700",
  failed: "bg-rose-100 text-rose-700",
};

export default function DeploymentPanel({
  run,
  onDownload,
  onRedeploy,
  redeploying,
}: {
  run: RunState | null;
  onDownload: () => void;
  onRedeploy: () => Promise<void>;
  redeploying: boolean;
}) {
  const deployment = run?.deployment ?? ({
    status: "not_started",
    url: null,
    port: null,
    attempts: 0,
    logs: [],
  } as DeploymentInfo);
  const status = deployment.status ?? "not_started";

  // Re-deploy is only available if the deployment stage has been reached and
  // the app is not currently live.
  const deploymentStageReached =
    run?.checkpoints?.some((cp) => cp.tag === "deploy" || cp.tag === "backend") ?? false;
  const canRedeploy = deploymentStageReached && status !== "running" && status !== "installing" && status !== "starting";

  return (
    <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Live Deployment</h2>
        <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${STATUS_COLOR[status] ?? "bg-slate-100 text-slate-600"}`}>
          {STATUS_LABEL[status] ?? status} {deployment.attempts ? `(attempt ${deployment.attempts})` : ""}
        </span>
      </div>

      {deployment.url ? (
        <a
          href={deployment.url}
          target="_blank"
          rel="noreferrer"
          className="mb-3 block truncate rounded-lg bg-emerald-50 px-3 py-2 font-mono text-sm text-emerald-700 underline"
        >
          {deployment.url}
        </a>
      ) : (
        <p className="mb-3 text-sm text-slate-400">The app will appear here once deployed to localhost.</p>
      )}

      <div className="mb-3 max-h-32 overflow-y-auto rounded-lg bg-slate-950 p-3 font-mono text-[11px] text-slate-300">
        {(deployment.logs?.length ?? 0) === 0 && <p className="text-slate-500">No deployment logs yet.</p>}
        {deployment.logs?.map((l, i) => <div key={i}>{l.message}</div>)}
      </div>

      {deployment.url && status === "running" && (
        <div className="mb-3">
          <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Live Preview (non-interactive)
          </p>
          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
            <iframe
              src={deployment.url}
              title="Deployment preview"
              className="pointer-events-none h-120 w-full"
              sandbox=""
              loading="lazy"
            />
          </div>
        </div>
      )}

      <div className="flex flex-col gap-2 sm:flex-row">
        <button
          onClick={onDownload}
          className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
        >
          Download full project repository (.zip)
        </button>
        {canRedeploy && (
          <button
            onClick={onRedeploy}
            disabled={redeploying}
            className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-50"
          >
            {redeploying ? "Re-deploying..." : "Re-deploy"}
          </button>
        )}
      </div>
      {!deploymentStageReached && (
        <p className="mt-2 text-xs text-slate-400">
          Re-deploy will be available once the project has reached the deployment stage.
        </p>
      )}
    </div>
  );
}
