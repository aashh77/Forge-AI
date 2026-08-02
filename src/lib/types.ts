// Shared shapes mirroring python-agents/models.py so the dashboard can be
// strongly typed against the agent engine's JSON responses.

export type AgentName =
  | "architect"
  | "planner"
  | "backend"
  | "frontend"
  | "qa"
  | "security"
  | "reviewer"
  | "supervisor"
  | "deploy";

export const AGENT_NAMES: AgentName[] = [
  "architect",
  "planner",
  "backend",
  "frontend",
  "qa",
  "security",
  "reviewer",
  "supervisor",
  "deploy",
];

export type AgentStatus = "idle" | "pending" | "running" | "success" | "failed";

export interface LogEntry {
  ts: number;
  message: string;
  level: "info" | "success" | "warning" | "error";
}

export interface Decision {
  id: string;
  ts: number;
  topic: string;
  chosen: string;
  justification: string;
  [key: string]: unknown;
}

export interface Commit {
  id: string;
  ts: number;
  message: string;
  files: string[];
}

export interface AgentState {
  name: AgentName;
  status: AgentStatus;
  progress: number;
  logs: LogEntry[];
  decisions: Decision[];
  commits: Commit[];
  started_at: number | null;
  finished_at: number | null;
  retries: number;
  error: string | null;
}

export interface Checkpoint {
  number: number;
  id: string;
  description: string;
  tag: string;
  ts: number;
}

export interface DebateTurn {
  round: number;
  agent: string;
  argument: string;
  concede: boolean;
}

export interface Debate {
  topic: string;
  positions: Array<{ agent: string; chosen: string; justification: string }>;
  transcript: DebateTurn[];
  verdict: { winner: string; justification: string; confidence: number };
  doc: string;
  ts: number;
}

export interface DeploymentInfo {
  status: "not_started" | "installing" | "starting" | "running" | "not_live" | "failed";
  url: string | null;
  port: number | null;
  attempts: number;
  logs: Array<{ ts: number; message: string }>;
}

export interface ChatAnswer {
  reason: string;
  evidence: string;
  confidence: number;
  alternative: string;
}

export interface ChatHistoryEntry {
  question: string;
  answer: ChatAnswer;
}

export interface TraceStep {
  layer: string;
  is_bottleneck: boolean;
  analysis: string;
  evidence: string;
  suggested_fix: string;
}

export interface Incident {
  question: string;
  trace: TraceStep[];
  bottleneck: TraceStep | null;
  benchmark: Record<string, unknown>;
  report: string;
  ts: number;
}

export interface ActiveDebug {
  question: string;
  status: "tracing" | "fixing" | "benchmarking" | "done";
  step?: string;
  trace: TraceStep[];
  bottleneck?: TraceStep | null;
  benchmark?: Record<string, unknown>;
}

export interface ReliabilityScorecard {
  code_quality?: number;
  security?: number;
  architecture?: number;
  test_coverage?: number;
  hallucination_risk?: number;
  complexity?: "low" | "medium" | "high";
  estimated_bugs?: number;
}

export interface RegressionEntry {
  run_id: string;
  ts: number;
  tests_passed_pct: number | null;
  compilation_success_pct: number;
  reliability_avg: number | null;
}

export interface RunStats {
  compilation_success_pct?: number;
  tests_passed_pct?: number | null;
  pr_acceptance_pct?: number;
  latency_seconds?: number;
  token_usage?: number;
  cost_usd?: number;
  reliability_avg?: number | null;
  regression_history?: RegressionEntry[];
}

export interface RunState {
  id: string;
  prompt: string;
  status: "pending" | "running" | "completed" | "failed" | "rolled_back" | "paused" | "stopped" | "suspended";
  error: string | null;
  created_at: number;
  updated_at: number;
  paused_at?: number | null;
  agents: Record<AgentName, AgentState>;
  checkpoints: Checkpoint[];
  debates: Debate[];
  chat_history: Record<AgentName, ChatHistoryEntry[]>;
  deployment: DeploymentInfo;
  reliability: ReliabilityScorecard;
  stats: RunStats;
  incidents: Incident[];
  active_debug: ActiveDebug | null;
  control?: {
    paused: boolean;
    stopped: boolean;
    resume_stage: number;
  };
  pipeline_context?: Record<string, unknown>;
}

export interface RunSummary {
  id: string;
  name: string;
  prompt: string;
  status: string;
  created_at: number;
  updated_at: number;
}
