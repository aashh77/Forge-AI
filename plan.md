# Forge AI — Original Build Plan

This document captures the plan for building the requested high-level application.
It covers the goals, stack, architecture, agent design, UI and deployment strategy.

---

## 1. Goal

Build a **single-page build dashboard** where a user describes software they want, and a team of specialised AI agents designs, plans, builds, tests, secures, reviews and deploys it end-to-end — with full observability and traceability.

Key user promises:
- Type a prompt, click "Forge It", watch agents work live.
- Inspect every agent's logs, decisions and justifications.
- Chat with individual agents.
- Download the generated project as a `.zip`.
- Pause, resume, stop and roll back runs.

---

## 2. High-Level Stack

| Layer | Technology | Why |
|-------|------------|-----|
| Dashboard UI | Next.js 16 (App Router), React 19, Tailwind CSS 4 | Fast SSR, modern React, easy styling |
| Database | PostgreSQL + Drizzle ORM | Persistent history, mirrored run states |
| API | Next.js API routes | Server-side bridge to the agent engine; keeps secrets safe |
| Agent engine | Python 3.11+, FastAPI | Lightweight, async-ready, easy LLM integration |
| LLM client | OpenAI-compatible client with retries/cost tracking | Provider-agnostic via base URL |
| Deployment | Localhost Node.js static/Express server | Zero external infrastructure by default |

---

## 3. Data Model

A single primary table is enough for the dashboard:

```sql
forge_runs (
  id text primary key,
  name text not null,
  prompt text not null,
  status text not null default 'pending',
  state jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
)
```

The Python engine is the source of truth while a run is active. Every poll from the dashboard mirrors the full run state into Postgres so history and reloads work even if the engine restarts.

---

## 4. Agent Design

Split the software lifecycle into 9 roles:

1. **Architect** — picks the stack and writes an ADR.
2. **Planner** — builds an execution schedule with dependencies.
3. **Backend** — generates Node/Express APIs and picks a datastore.
4. **Frontend** — generates vanilla HTML/CSS/JS UIs.
5. **QA** — writes and runs smoke/fuzz tests and scores quality.
6. **Security** — scans secrets, runs npm audit, reviews architecture and headers.
7. **Reviewer** — checks requirements and commits.
8. **Supervisor** — resolves conflicts, scores reliability, computes final stats.
9. **Deploy** — runs the generated app on localhost.

All agents share a base class for:
- Status/progress/logging
- Decision/commit recording
- LLM calls (JSON mode)
- File writing

Each agent returns structured JSON so the pipeline can act on it (e.g., schedule, findings, verdicts).

---

## 5. Pipeline Flow

```
User prompt
    │
    ▼
Architect ──► Planner ──► execute_schedule()
                              │
    ┌─────────────────────────┼─────────────────────────┐
    ▼                         ▼                         ▼
Backend/Frontend          Security/QA              Reviewer
    │                         │                         │
    └──────────► Deploy ◄─────┘                         │
                              │                         ▼
                              ▼                    Supervisor
                           Live URL              scoring + stats
```

- The Planner can interleave steps (e.g., security audit mid-frontend).
- Security/Reviewer findings can trigger Supervisor debates or Planner replans.
- Every agent step creates a checkpoint for rollback.

---

## 6. Dashboard UI Plan

Layout:
- Header with engine health badge.
- Prompt input + voice input + "Forge It" button.
- Left sidebar: project history (select, rename, delete).
- Main area:
  - Status + controls (pause/resume/stop).
  - Agent progress bars (click to inspect).
  - Agent detail: terminal, decisions, Q&A.
  - Deployment panel: URL, preview iframe, download, redeploy.
  - Checkpoints + debates.
  - Reliability scorecard + run stats.
  - Natural-language debugger.

Mobile strategy:
- Stack sidebar below main content on narrow screens.
- Wrap button groups and status chips.
- Use `clamp()` and `min()` for fluid sizing.
- Avoid fixed widths; rely on `min-w-0` and `break-words`.

---

## 7. Deployment Strategy

Generated projects must run locally without paid services:
- Backend projects use Express with `process.env.PORT` and `express.static('public')`.
- Static projects get a generated Node static server.
- The engine scans ports in a configurable range and health-checks `/api/health`.
- The dashboard proxies download requests and shows a non-interactive iframe preview.

For production hosting of the dashboard itself, target Vercel with a Postgres database.

---

## 8. Extensibility

- New agents can be added by inheriting `BaseAgent` and registering in `server.py`.
- New dashboard panels can be added as React components under `src/components/`.
- LLM provider can be swapped via environment variables.

---

## 9. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| LLM returns invalid JSON | Retry with temperature tuning; use fallback logic for critical paths. |
| Generated project fails to start | Deployment manager injects `/api/health`, creates fallback static server, retries. |
| Long-running runs block UI | Run pipeline in FastAPI background tasks; dashboard polls every 2.5s. |
| Secrets in generated code | Security agent regex scan + autofix. |
| Mobile overflow | Fluid grids, wrapping flex rows, line-clamp, break-words. |

---

## 10. Success Criteria

- A user can type a prompt and receive a deployed, test-covered, reviewed project.
- The dashboard displays every agent's progress, logs and decisions in real time.
- The generated code is runnable on localhost with a single `npm install && npm start`.
- History persists across engine restarts.
