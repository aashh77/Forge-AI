"use client";

import { useEffect, useState } from "react";
import type { AgentName, AgentState, ChatAnswer, ChatHistoryEntry } from "@/lib/types";
import VoiceInputButton, { type VoiceTranscript } from "@/components/VoiceInputButton";

const LABELS: Record<AgentName, string> = {
  architect: "Architect Agent",
  planner: "Planner Agent",
  backend: "Backend Agent",
  frontend: "Frontend Agent",
  qa: "QA Agent",
  security: "Security Agent",
  reviewer: "Reviewer Agent",
  supervisor: "Supervisor Agent",
  deploy: "Deploy Agent",
};

function levelColor(level: string): string {
  switch (level) {
    case "success":
      return "text-emerald-600";
    case "error":
      return "text-rose-600";
    case "warning":
      return "text-amber-600";
    default:
      return "text-slate-500";
  }
}

export default function AgentDetail({
  agentName,
  agent,
  chatHistory,
  onAsk,
}: {
  agentName: AgentName | null;
  agent: AgentState | null | undefined;
  chatHistory: ChatHistoryEntry[];
  onAsk: (question: string) => Promise<unknown>;
}) {
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
  const [voiceOriginal, setVoiceOriginal] = useState<string | null>(null);
  const [voiceIntent, setVoiceIntent] = useState<string | null>(null);

  // Clear the pending placeholder once the server has recorded the question.
  useEffect(() => {
    if (pendingQuestion && chatHistory.some((e) => e.question === pendingQuestion)) {
      setPendingQuestion(null);
    }
  }, [chatHistory, pendingQuestion]);

  if (!agentName) {
    return (
      <div className="rounded-2xl bg-white p-6 text-sm text-slate-500 shadow-sm ring-1 ring-slate-200">
        Click an agent on the left to watch its live thinking, decisions and justification
        documents, and to ask it questions directly (e.g. &ldquo;Why did Backend choose
        Redis?&rdquo;).
      </div>
    );
  }

  const submit = async () => {
    if (!question.trim() || asking) return;
    const q = question.trim();
    setQuestion("");
    setVoiceOriginal(null);
    setVoiceIntent(null);
    setPendingQuestion(q);
    setAsking(true);
    try {
      await onAsk(q);
    } catch (err) {
      // Clear pending on error; the question was not recorded.
      setPendingQuestion(null);
      console.error(err);
    } finally {
      setAsking(false);
    }
  };

  const handleVoice = (result: VoiceTranscript) => {
    setQuestion(result.transcript);
    if (result.original) {
      setVoiceOriginal(result.original);
      setVoiceIntent(result.intentNote || null);
    } else {
      setVoiceOriginal(null);
      setVoiceIntent(null);
    }
  };

  const pendingAnswer: ChatAnswer = {
    reason: "Answering...",
    evidence: "",
    confidence: 0,
    alternative: "",
  };
  const displayHistory: ChatHistoryEntry[] = pendingQuestion
    ? [{ question: pendingQuestion, answer: pendingAnswer }, ...chatHistory]
    : chatHistory;

  return (
    <div className="flex h-full flex-col rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-semibold text-slate-900">{LABELS[agentName]}</h2>
        <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
          {agent?.status ?? "idle"}
        </span>
      </div>

      <div className="mb-4 max-h-72 overflow-y-auto rounded-lg bg-slate-950 p-3 font-mono text-xs text-slate-200">
        {(agent?.logs?.length ?? 0) === 0 && <p className="text-slate-500">No activity yet.</p>}
        {agent?.logs?.map((log, i) => (
          <div key={i} className={`break-words ${levelColor(log.level)}`}>
            {log.level === "error" ? "✗ " : log.level === "success" ? "✓ " : "› "}
            {log.message}
          </div>
        ))}
      </div>

      {(agent?.decisions?.length ?? 0) > 0 && (
        <div className="mb-4">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Decisions, Justifications &amp; Trade-offs
          </h3>
          <div className="flex flex-col gap-2">
            {agent!.decisions.map((d) => (
              <div key={d.id} className="rounded-lg border border-slate-200 p-3 text-sm break-words">
                <div className="font-medium text-slate-800">
                  {d.topic}: <span className="text-slate-900">{d.chosen}</span>
                  {typeof d.confidence === "number" && (
                    <span className="ml-2 text-[11px] font-normal text-slate-500">
                      ({d.confidence}% confidence)
                    </span>
                  )}
                </div>
                <p className="mt-1 text-xs text-slate-600">{d.justification}</p>
                {Array.isArray(d.ctq) && d.ctq.length > 0 && (
                  <p className="mt-1 text-xs text-slate-600">
                    <span className="font-semibold">Conditions considered:</span>{" "}
                    {d.ctq.join("; ")}
                  </p>
                )}
                {Array.isArray(d.alternatives) && d.alternatives.length > 0 && (
                  <div className="mt-2 text-xs text-slate-500">
                    <span className="font-semibold">Alternatives rejected:</span>
                    <ul className="ml-4 mt-0.5 list-disc">
                      {d.alternatives.map((alt, idx) => (
                        <li key={idx}>
                          {typeof alt === "object" && alt !== null
                            ? `${(alt as { name?: string }).name ?? JSON.stringify(alt)} — ${
                                (alt as { why_rejected?: string }).why_rejected ?? ""
                              }`
                            : String(alt)}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {Array.isArray(d.options) && d.options.length > 0 && (
                  <div className="mt-2 text-xs text-slate-500">
                    <span className="font-semibold">Other options evaluated:</span>{" "}
                    {d.options.map((o, idx) => (typeof o === "string" ? o : JSON.stringify(o))).join("; ")}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-auto border-t border-slate-100 pt-4">
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Ask {LABELS[agentName]}
        </h3>
        <div className="flex gap-2">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            placeholder={`e.g. Why did ${agentName} choose this approach?`}
            className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500"
          />
          <VoiceInputButton onTranscript={handleVoice} disabled={asking} />
          <button
            onClick={submit}
            disabled={asking}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {asking ? "Asking..." : "Ask"}
          </button>
        </div>
        {voiceOriginal && (
          <p className="mt-1.5 text-xs text-slate-500">
            Original Hindi: {voiceOriginal}
            {voiceIntent ? ` · Intent: ${voiceIntent}` : ""}
          </p>
        )}

        <div className="mt-3 flex flex-col gap-3">
          {[...displayHistory].reverse().map((entry, i) => (
            <div key={i} className="rounded-lg bg-slate-50 p-3 text-sm">
              <p className="font-medium text-slate-800">Q: {entry.question}</p>
              <p className="mt-1 text-slate-700">
                <span className="font-semibold">Reason:</span> {entry.answer.reason}
              </p>
              <p className="mt-1 text-slate-600">
                <span className="font-semibold">Evidence:</span> {entry.answer.evidence}
              </p>
              <p className="mt-1 text-slate-600">
                <span className="font-semibold">Confidence:</span> {entry.answer.confidence}%
              </p>
              <p className="mt-1 text-slate-600">
                <span className="font-semibold">Alternative:</span> {entry.answer.alternative}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
