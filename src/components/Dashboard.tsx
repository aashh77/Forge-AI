"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import AgentBars from "@/components/AgentBars";
import AgentDetail from "@/components/AgentDetail";
import HistoryPanel from "@/components/HistoryPanel";
import ScorePanels from "@/components/ScorePanels";
import DeploymentPanel from "@/components/DeploymentPanel";
import DebuggerPanel from "@/components/DebuggerPanel";
import RunHistory from "@/components/RunHistory";
import VoiceInputButton, { type VoiceTranscript } from "@/components/VoiceInputButton";
import type { AgentName, RunState, RunSummary } from "@/lib/types";

interface EngineHealth {
  reachable: boolean;
  llm_configured?: boolean;
  llm_problems?: string[];
  provider?: string;
  model?: string;
  error?: string;
}

export default function Dashboard() {
  const [prompt, setPrompt] = useState(
    "Build authentication with OAuth, RBAC, audit logs, tests and deployment.",
  );
  const [runId, setRunId] = useState<string | null>(null);
  const [run, setRun] = useState<RunState | null>(null);
  const [history, setHistory] = useState<RunSummary[]>([]);
  const [engineHealth, setEngineHealth] = useState<EngineHealth | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<AgentName | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [rollingBack, setRollingBack] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [redeploying, setRedeploying] = useState(false);
  const [controlBusy, setControlBusy] = useState<"pause" | "resume" | "stop" | null>(null);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [voiceOriginal, setVoiceOriginal] = useState<string | null>(null);
  const [voiceIntent, setVoiceIntent] = useState<string | null>(null);

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const refreshHealth = useCallback(async () => {
    const res = await fetch("/api/forge/engine-health", { cache: "no-store" });
    setEngineHealth(await res.json());
  }, []);

  const refreshHistory = useCallback(async () => {
    const res = await fetch("/api/forge", { cache: "no-store" });
    const data = await res.json();
    setHistory(Array.isArray(data.runs) ? data.runs : []);
  }, []);

  const refreshRun = useCallback(async (id: string) => {
    const res = await fetch(`/api/forge/${id}`, { cache: "no-store" });
    if (res.ok) {
      setRun(await res.json());
    }
  }, []);

  useEffect(() => {
    refreshHealth();
    refreshHistory();
    const interval = setInterval(refreshHealth, 10000);
    return () => clearInterval(interval);
  }, [refreshHealth, refreshHistory]);

  useEffect(() => {
    if (pollRef.current) clearInterval(pollRef.current);
    if (!runId) return;
    refreshRun(runId);
    pollRef.current = setInterval(() => refreshRun(runId), 2500);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [runId, refreshRun]);

  const startRun = async () => {
    if (!prompt.trim() || submitting) return;
    setSubmitting(true);
    setFormError(null);
    try {
      const res = await fetch("/api/forge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: prompt.trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        setFormError(data.error || "Failed to start run");
        return;
      }
      setRunId(data.run_id);
      setSelectedAgent(null);
      refreshHistory();
    } catch (err) {
      setFormError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  };

  const askAgent = async (agent: AgentName, question: string) => {
    if (!runId) return;
    const res = await fetch(`/api/forge/${runId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ agent, question }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || "Failed to ask agent");
    }
    await refreshRun(runId);
    return data;
  };

  const rollback = async (checkpointId: string) => {
    if (!runId) return;
    setRollingBack(checkpointId);
    try {
      await fetch(`/api/forge/${runId}/rollback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ checkpoint_id: checkpointId }),
      });
      await refreshRun(runId);
    } finally {
      setRollingBack(null);
    }
  };

  const askDebugger = async (question: string) => {
    if (!runId) return;
    await fetch(`/api/forge/${runId}/debug`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    await refreshRun(runId);
  };

  const download = () => {
    if (!runId) return;
    window.open(`/api/forge/${runId}/download`, "_blank");
  };

  const redeploy = async () => {
    if (!runId) return;
    setRedeploying(true);
    try {
      const res = await fetch(`/api/forge/${runId}/redeploy`, { method: "POST" });
      if (!res.ok) {
        const data = await res.json();
        setFormError(data.error || "Re-deploy failed");
      }
      await refreshRun(runId);
    } catch (err) {
      setFormError((err as Error).message);
    } finally {
      setRedeploying(false);
    }
  };

  const pause = async () => {
    if (!runId) return;
    setControlBusy("pause");
    try {
      await fetch(`/api/forge/${runId}/pause`, { method: "POST" });
      await refreshRun(runId);
    } catch (err) {
      setFormError((err as Error).message);
    } finally {
      setControlBusy(null);
    }
  };

  const resume = async () => {
    if (!runId) return;
    setControlBusy("resume");
    try {
      await fetch(`/api/forge/${runId}/resume`, { method: "POST" });
      await refreshRun(runId);
    } catch (err) {
      setFormError((err as Error).message);
    } finally {
      setControlBusy(null);
    }
  };

  const stop = async () => {
    if (!runId) return;
    const confirmed = window.confirm(
      "Stop this run? This will cancel it after the current agent finishes and cannot be resumed."
    );
    if (!confirmed) return;
    setControlBusy("stop");
    try {
      await fetch(`/api/forge/${runId}/stop`, { method: "POST" });
      await refreshRun(runId);
    } catch (err) {
      setFormError((err as Error).message);
    } finally {
      setControlBusy(null);
    }
  };

  const renameRun = async (id: string, name: string) => {
    setRenamingId(id);
    try {
      const res = await fetch(`/api/forge/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      if (res.ok) await refreshHistory();
    } finally {
      setRenamingId(null);
    }
  };

  const deleteRun = async (id: string) => {
    const confirmed = window.confirm("Delete this project from history?");
    if (!confirmed) return;
    setDeletingId(id);
    try {
      const res = await fetch(`/api/forge/${id}`, { method: "DELETE" });
      if (res.ok) {
        await refreshHistory();
        if (runId === id) {
          setRunId(null);
          setRun(null);
        }
      }
    } finally {
      setDeletingId(null);
    }
  };

  const selectedAgentState = selectedAgent && run ? run.agents?.[selectedAgent] : null;
  const selectedChatHistory = selectedAgent && run ? run.chat_history?.[selectedAgent] ?? [] : [];

  const canPause = run && (run.status === "running" || run.status === "pending");
  const canResume = run && run.status === "paused";
  const canStop = run && (run.status === "running" || run.status === "pending" || run.status === "paused");

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      <header className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Forge AI</p>
          <h1 className="mt-1 text-2xl font-bold text-slate-950 break-words sm:text-3xl">Autonomous Software Engineering War Room</h1>
          <p className="mt-2 max-w-2xl text-sm text-slate-600">
            Seven specialised agents plus a Supervisor design, plan, build, test, secure, review
            and deploy your request end-to-end — live, on this dashboard.
          </p>
        </div>
        <div
          className={`rounded-full px-3 py-1.5 text-xs font-medium ${
            engineHealth?.reachable && engineHealth.llm_configured
              ? "bg-emerald-100 text-emerald-700"
              : "bg-amber-100 text-amber-700"
          }`}
        >
          {engineHealth?.reachable
            ? engineHealth.llm_configured
              ? `Agent engine online · ${engineHealth.model}`
              : "Agent engine online · LLM not configured (see python-agents/.env)"
            : "Agent engine offline — start python-agents/server.py"}
        </div>
      </header>

      <section className="mb-6 rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-500">
          Describe what to build
        </label>
        <div className="flex flex-col gap-3 sm:flex-row">
          <div className="flex flex-1 flex-col gap-2 sm:flex-row">
            <textarea
              value={prompt}
              onChange={(e) => {
                setPrompt(e.target.value);
                if (!e.target.value.trim()) {
                  setVoiceOriginal(null);
                  setVoiceIntent(null);
                }
              }}
              rows={2}
              className="min-w-0 flex-1 resize-none rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-slate-500"
            />
            <VoiceInputButton
              onTranscript={(result: VoiceTranscript) => {
                setPrompt(result.transcript);
                if (result.original) {
                  setVoiceOriginal(result.original);
                  setVoiceIntent(result.intentNote || null);
                } else {
                  setVoiceOriginal(null);
                  setVoiceIntent(null);
                }
              }}
              disabled={submitting}
            />
          </div>
          <button
            onClick={() => {
              setVoiceOriginal(null);
              setVoiceIntent(null);
              void startRun();
            }}
            disabled={submitting}
            className="shrink-0 rounded-xl bg-slate-900 px-6 py-3 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50"
          >
            {submitting ? "Waking agents..." : "Forge It"}
          </button>
        </div>
        {voiceOriginal && (
          <p className="mt-2 text-xs text-slate-500">
            Original Hindi: {voiceOriginal}
            {voiceIntent ? ` · Intent preserved: ${voiceIntent}` : ""}
          </p>
        )}
        {formError && <p className="mt-2 text-sm text-rose-600">{formError}</p>}
      </section>

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <aside className="order-2 lg:order-1">
          <RunHistory
            runs={history}
            activeRunId={runId}
            onSelect={(id) => {
              const selected = history.find((r) => r.id === id);
              if (selected) setPrompt(selected.prompt);
              setRunId(id);
              setSelectedAgent(null);
            }}
            onRename={renameRun}
            onDelete={deleteRun}
            renamingId={renamingId}
            deletingId={deletingId}
          />
        </aside>

        <main className="order-1 lg:order-2 min-w-0">
          {run && (
            <>
              {(run.status === "failed" || run.status === "stopped" || run.status === "suspended") && run.error && (
                <div className="mb-6 rounded-xl bg-rose-50 p-4 text-sm text-rose-700 ring-1 ring-rose-200">
                  {run.status === "suspended" ? "Run suspended: " : "Run stopped/failed: "}
                  {run.error}
                </div>
              )}

              <div className="mb-6 flex flex-wrap items-center gap-2">
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                  Status: {run.status}
                </span>
                {canPause && (
                  <button
                    onClick={pause}
                    disabled={!!controlBusy}
                    className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-700 hover:bg-amber-200 disabled:opacity-50"
                  >
                    {controlBusy === "pause" ? "Pausing..." : "Pause"}
                  </button>
                )}
                {canResume && (
                  <button
                    onClick={resume}
                    disabled={!!controlBusy}
                    className="rounded-full bg-sky-100 px-3 py-1 text-xs font-medium text-sky-700 hover:bg-sky-200 disabled:opacity-50"
                  >
                    {controlBusy === "resume" ? "Resuming..." : "Resume"}
                  </button>
                )}
                {canStop && (
                  <button
                    onClick={stop}
                    disabled={!!controlBusy}
                    className="rounded-full bg-rose-100 px-3 py-1 text-xs font-medium text-rose-700 hover:bg-rose-200 disabled:opacity-50"
                  >
                    {controlBusy === "stop" ? "Stopping..." : "Stop"}
                  </button>
                )}
                {run.status === "paused" && (
                  <span className="text-xs text-slate-500">
                    Resume is available for ~20 minutes after pausing.
                  </span>
                )}
              </div>

              <div className="mb-6 grid gap-6 lg:grid-cols-[280px_1fr]">
                <AgentBars agents={run.agents} selected={selectedAgent} onSelect={setSelectedAgent} />
                <AgentDetail
                  agentName={selectedAgent}
                  agent={selectedAgentState}
                  chatHistory={selectedChatHistory}
                  onAsk={(q) => askAgent(selectedAgent as AgentName, q)}
                />
              </div>

              <div className="mb-6">
                <DeploymentPanel run={run} onDownload={download} onRedeploy={redeploy} redeploying={redeploying} />
              </div>

              <div className="mb-6">
                <HistoryPanel
                  checkpoints={run.checkpoints}
                  debates={run.debates}
                  onRollback={rollback}
                  rollingBack={rollingBack}
                />
              </div>

              <div className="mb-6">
                <ScorePanels reliability={run.reliability} stats={run.stats} />
              </div>

              <div className="mb-6">
                <DebuggerPanel
                  activeDebug={run.active_debug}
                  incidents={run.incidents}
                  onAsk={askDebugger}
                  disabled={run.status !== "completed"}
                />
              </div>
            </>
          )}

          {!run && (
            <div className="rounded-2xl border-2 border-dashed border-slate-300 p-12 text-center text-sm text-slate-500">
              Describe a feature above and click &ldquo;Forge It&rdquo; to watch the agents wake up,
              or select a project from the history tab to review its full history.
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
