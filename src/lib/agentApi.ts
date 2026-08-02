// Server-side helper for calling the Forge AI Python agent engine. Only
// used from Next.js API routes (never from the browser) so the engine URL
// and any future auth never leak to the client bundle.

const AGENT_API_URL = (process.env.AGENT_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

export class AgentApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${AGENT_API_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
      cache: "no-store",
      signal: AbortSignal.timeout(15000),
    });
  } catch {
    throw new AgentApiError(
      `Cannot reach the Forge AI agent engine at ${AGENT_API_URL}. Make sure it is running ` +
        `(see python-agents/README.md) and AGENT_API_URL is set correctly.`,
      503,
    );
  }
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const message = (data && (data.detail || data.message)) || `Agent engine returned ${res.status}`;
    throw new AgentApiError(message, res.status);
  }
  return data as T;
}

export const agentApi = {
  health: () => request<{ ok: boolean; llm_configured: boolean; llm_problems: string[]; provider: string; model: string }>("/health"),
  listRuns: () => request<{ runs: unknown[] }>("/runs"),
  createRun: (prompt: string, runId: string) =>
    request<{ run_id: string }>("/runs", { method: "POST", body: JSON.stringify({ prompt, run_id: runId }) }),
  getRun: (runId: string) => request<unknown>(`/runs/${encodeURIComponent(runId)}`),
  chat: (runId: string, agent: string, question: string) =>
    request<unknown>(`/runs/${encodeURIComponent(runId)}/chat`, {
      method: "POST",
      body: JSON.stringify({ agent, question }),
    }),
  translate: (text: string, sourceLang: string = "hi", targetLang: string = "en") =>
    request<{ original: string; translated: string; intent_note: string }>("/translate", {
      method: "POST",
      body: JSON.stringify({ text, source_lang: sourceLang, target_lang: targetLang }),
    }),
  checkpoints: (runId: string) => request<unknown>(`/runs/${encodeURIComponent(runId)}/checkpoints`),
  rollback: (runId: string, checkpointId: string) =>
    request<unknown>(`/runs/${encodeURIComponent(runId)}/rollback`, {
      method: "POST",
      body: JSON.stringify({ checkpoint_id: checkpointId }),
    }),
  debug: (runId: string, question: string) =>
    request<unknown>(`/runs/${encodeURIComponent(runId)}/debug`, {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
  pause: (runId: string) =>
    request<unknown>(`/runs/${encodeURIComponent(runId)}/pause`, { method: "POST" }),
  resume: (runId: string) =>
    request<unknown>(`/runs/${encodeURIComponent(runId)}/resume`, { method: "POST" }),
  stop: (runId: string) =>
    request<unknown>(`/runs/${encodeURIComponent(runId)}/stop`, { method: "POST" }),
  redeploy: (runId: string) =>
    request<unknown>(`/runs/${encodeURIComponent(runId)}/redeploy`, { method: "POST" }),
  deploymentStatus: (runId: string) =>
    request<unknown>(`/runs/${encodeURIComponent(runId)}/deployment-status`),
  downloadUrl: (runId: string) => `${AGENT_API_URL}/runs/${encodeURIComponent(runId)}/download`,
};

export { AGENT_API_URL };
