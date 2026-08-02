"use client";

import type { ReliabilityScorecard, RunStats } from "@/lib/types";

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg bg-slate-50 p-3">
      <p className="text-[11px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-slate-900">{value}</p>
    </div>
  );
}

export default function ScorePanels({ reliability, stats }: { reliability: ReliabilityScorecard; stats: RunStats }) {
  const hasReliability = Object.keys(reliability || {}).length > 0;
  const hasStats = Object.keys(stats || {}).length > 0;

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          AI Reliability Scorecard
        </h2>
        {!hasReliability && <p className="text-sm text-slate-400">Scored once the run completes.</p>}
        {hasReliability && (
          <div className="grid grid-cols-2 gap-2">
            <Metric label="Code Quality" value={fmtPct(reliability.code_quality)} />
            <Metric label="Security" value={fmtPct(reliability.security)} />
            <Metric label="Architecture" value={fmtPct(reliability.architecture)} />
            <Metric label="Test Coverage" value={fmtPct(reliability.test_coverage)} />
            <Metric label="Hallucination Risk" value={fmtPct(reliability.hallucination_risk)} />
            <Metric label="Complexity" value={reliability.complexity ?? "—"} />
            <Metric label="Estimated Bugs" value={reliability.estimated_bugs ?? "—"} />
          </div>
        )}
      </div>

      <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">Final Run Stats</h2>
        {!hasStats && <p className="text-sm text-slate-400">Computed once the run completes.</p>}
        {hasStats && (
          <div className="grid grid-cols-2 gap-2">
            <Metric label="Compilation Success" value={fmtPct(stats.compilation_success_pct)} />
            <Metric label="Tests Passed" value={fmtPct(stats.tests_passed_pct ?? undefined)} />
            <Metric label="PR Acceptance" value={fmtPct(stats.pr_acceptance_pct)} />
            <Metric label="Latency" value={`${stats.latency_seconds ?? 0}s`} />
            <Metric label="Token Usage" value={stats.token_usage ?? 0} />
            <Metric label="Cost" value={`$${(stats.cost_usd ?? 0).toFixed(4)}`} />
            <Metric label="Reliability Avg" value={fmtPct(stats.reliability_avg ?? undefined)} />
          </div>
        )}
        {(stats.regression_history?.length ?? 0) > 0 && (
          <div className="mt-4">
            <p className="mb-1 text-[11px] uppercase tracking-wide text-slate-500">Regression History</p>
            <div className="flex items-end gap-1">
              {stats.regression_history!.slice(-20).map((r, i) => (
                <div
                  key={i}
                  title={`${r.run_id}: ${r.tests_passed_pct ?? "—"}% tests`}
                  className="w-3 rounded-t bg-slate-800"
                  style={{ height: `${Math.max(4, r.tests_passed_pct ?? 4)}px` }}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function fmtPct(v: number | undefined): string {
  return v === undefined || v === null ? "—" : `${v}%`;
}
