"use client";

import { useState } from "react";
import type { ActiveDebug, Incident } from "@/lib/types";
import VoiceInputButton, { type VoiceTranscript } from "@/components/VoiceInputButton";

export default function DebuggerPanel({
  activeDebug,
  incidents,
  onAsk,
  disabled,
}: {
  activeDebug: ActiveDebug | null;
  incidents: Incident[];
  onAsk: (question: string) => Promise<unknown>;
  disabled: boolean;
}) {
  const [question, setQuestion] = useState("");
  const [sending, setSending] = useState(false);
  const [voiceOriginal, setVoiceOriginal] = useState<string | null>(null);
  const [voiceIntent, setVoiceIntent] = useState<string | null>(null);

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

  const submit = async () => {
    if (!question.trim() || sending) return;
    setSending(true);
    try {
      await onAsk(question.trim());
      setQuestion("");
      setVoiceOriginal(null);
      setVoiceIntent(null);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
        Natural Language Debugger
      </h2>
      <div className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          placeholder="e.g. Why is login slow?"
          disabled={disabled}
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500 disabled:bg-slate-50"
        />
        <VoiceInputButton onTranscript={handleVoice} disabled={disabled || sending} />
        <button
          onClick={submit}
          disabled={disabled || sending}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {sending ? "Tracing..." : "Ask"}
        </button>
      </div>
      {voiceOriginal && (
        <p className="mt-1.5 text-xs text-slate-500">
          Original Hindi: {voiceOriginal}
          {voiceIntent ? ` · Intent: ${voiceIntent}` : ""}
        </p>
      )}

      {activeDebug && (
        <div className="mt-4 rounded-lg border border-slate-200 p-3">
          <p className="mb-2 text-xs font-semibold text-slate-600">
            &ldquo;{activeDebug.question}&rdquo; — status: {activeDebug.status}
          </p>
          <div className="flex flex-wrap items-center gap-1 font-mono text-xs">
            {activeDebug.trace.map((t, i) => (
              <span key={i} className="flex items-center gap-1">
                <span
                  className={`rounded-full px-2 py-1 ${
                    t.is_bottleneck ? "bg-rose-100 text-rose-700" : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {t.layer}
                </span>
                {i < activeDebug.trace.length - 1 && <span>↓</span>}
              </span>
            ))}
          </div>
          {activeDebug.bottleneck && (
            <p className="mt-2 text-xs text-slate-700">
              <span className="font-semibold">Bottleneck:</span> {activeDebug.bottleneck.analysis}
            </p>
          )}
          {activeDebug.benchmark && Object.keys(activeDebug.benchmark).length > 0 && (
            <p className="mt-1 break-words text-xs text-slate-500">
              Benchmark: {JSON.stringify(activeDebug.benchmark)}
            </p>
          )}
        </div>
      )}

      {incidents.length > 0 && (
        <div className="mt-4">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Incident Reports</p>
          <div className="flex flex-col gap-2">
            {[...incidents].reverse().map((inc, i) => (
              <div key={i} className="rounded-lg bg-slate-50 p-3 text-xs">
                <p className="font-medium text-slate-800">{inc.question}</p>
                <p className="mt-1 text-slate-600">
                  Root cause: {inc.bottleneck?.analysis ?? "No clear bottleneck identified."}
                </p>
                <p className="mt-1 text-slate-500">Report saved: {inc.report}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
