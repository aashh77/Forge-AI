# Forge AI — Agent Engine (Python)

This is the real multi-agent brain behind Forge AI: **8 agents** (Architect,
Planner, Backend, Frontend, QA, Security, Reviewer, Supervisor) built in
Python, each of which calls a real LLM API (OpenAI-compatible) to design,
plan, build, test, secure, review and deploy whatever you ask for — then
generates a downloadable project repository.

**There is no hardcoded AI logic anywhere in this codebase.** Every
document, decision, piece of generated code, debate argument, and score is
produced by a real call to the LLM configured in `.env`. If you don't
provide an API key, runs will fail fast with a clear configuration error —
they will never fall back to canned/fake output.

## What it actually does

1. **Architect Agent** — produces two architecture options with pros/cons/CTQ,
   picks one, writes an ADR + Mermaid diagram.
2. **Planner Agent** — breaks the project into justified issues + a
   dependency graph, proposes two schedules, picks the best one.
3. **Backend Agent** — picks a database (with a justification doc),
   generates a real, runnable Node.js/Express API + business logic.
4. **Frontend Agent** — generates a real static UI (HTML/CSS/JS) wired to
   the backend API, with accessibility notes, state management approach and
   user configuration.
5. **QA Agent** — writes real smoke tests + edge cases + fuzz payloads and runs
   them against the *actually deployed* app. If LLM test generation is slow or
   fails, it falls back to deterministic health/root checks so the pipeline
   never hangs waiting for a model response.
6. **Security Agent** — scans for hardcoded secrets, runs `npm audit`,
   produces an OWASP-style threat model + permission analysis, and
   auto-fixes what it can.
7. **Reviewer Agent** — reviews every commit made by every other agent,
   approves/rejects with comments and suggestions.
8. **Supervisor Agent** — watches every agent, detects disagreements between
   them (e.g. Backend vs Security on data-access pattern), runs a real
   multi-round LLM **Debate Mode**, declares a winner with justification,
   and produces the final **AI Reliability Scorecard** + run statistics.

Along the way, the engine:

- **Deploys the generated app on localhost automatically** — runs
  `npm install`, starts the server, polls `GET /api/health` until it's
  reachable, and **self-heals** (feeds the real error back to the Backend
  Agent, patches the code, retries) up to `MAX_BUILD_RETRIES` times.
- Creates a **checkpoint** after every major decision, so any run can be
  **rolled back** to an earlier state (self-healing on regressions).
- Exposes a **chat endpoint** so you can ask any agent "why" it made a
  decision, grounded only in that agent's own recorded decisions.
- Exposes a **Natural Language Debugger**: ask a question like *"Why is
  login slow?"*, and the engine snapshots a checkpoint, traces
  Frontend → Backend → Security(data layer) → QA(runtime), identifies the
  likely bottleneck, patches the code, redeploys, benchmarks, and writes an
  incident report.
- Lets you **download the full run as a ZIP** (source code, docs, ADRs,
  justification reports, debate transcripts, incident reports, full agent
  state).

## Requirements

- Python 3.10+
- Node.js 18+ and npm (used to install/build/run the *generated* projects —
  not required to run the agent engine itself, but required for it to be
  able to deploy anything)
- An API key for any OpenAI-compatible Chat Completions endpoint (OpenAI,
  OpenRouter, Groq, Together AI, Fireworks, a local vLLM/Ollama OpenAI
  shim, etc.)

## 1. Configure

```bash
cd python-agents
cp .env.example .env
```

Edit `.env` and set at minimum:

```dotenv
OPENAI_API_KEY=sk-...your real key...
OPENAI_MODEL=gpt-4o-mini
```

Everything else has sensible defaults (retry limits, port range, timeouts —
see `.env.example` for the full list). **No code changes are ever
required** — the whole system reads its behaviour from this file.

## 2. Install & run

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python server.py
# or: uvicorn server:app --host 0.0.0.0 --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Verify it's healthy:

```bash
curl http://localhost:8000/health
```

## 3. Use it

The **Forge AI dashboard** (the Next.js app in the parent folder built with the help of OpenAI Codex) is the
intended UI — see the root `README.md` to run it. It talks to this engine
over HTTP using the `AGENT_API_URL` environment variable (defaults to
`http://127.0.0.1:8000`), so just start both and open the dashboard.

You can also drive the engine directly with curl:

```bash
# Kick off a run
curl -s -X POST http://localhost:8000/runs \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Build authentication with OAuth, RBAC, audit logs, tests and deployment"}'
# -> {"run_id": "run-xxxxxxxxxxxx"}

# Poll full state (agents, logs, decisions, checkpoints, debates, deployment url, stats...)
curl -s http://localhost:8000/runs/run-xxxxxxxxxxxx | python3 -m json.tool

# Ask an agent a question
curl -s -X POST http://localhost:8000/runs/run-xxxxxxxxxxxx/chat \
  -H 'Content-Type: application/json' \
  -d '{"agent":"backend","question":"Why did you choose this database?"}'

# Roll back to a checkpoint
curl -s -X POST http://localhost:8000/runs/run-xxxxxxxxxxxx/rollback \
  -H 'Content-Type: application/json' \
  -d '{"checkpoint_id":"cp-3"}'

# Natural language debugger
curl -s -X POST http://localhost:8000/runs/run-xxxxxxxxxxxx/debug \
  -H 'Content-Type: application/json' \
  -d '{"question":"Why is login slow?"}'

# Download the full project + docs + artifacts as a ZIP
curl -s -o forge-ai-run.zip http://localhost:8000/runs/run-xxxxxxxxxxxx/download
```

Everything a run produces lives on disk under `python-agents/workspace/<run_id>/`:

```
workspace/<run_id>/
  state.json          full agent state (logs, decisions, checkpoints, debates...)
  project/            the generated, runnable application
  docs/               ADRs, justification docs, security reports, debate
                       transcripts, incident reports, reliability scorecard
  checkpoints/<n>/     snapshot of project/ + state.json at that point
  server.log          stdout/stderr of the currently deployed app
```

## REST API reference

| Method | Path                              | Purpose                                             |
|--------|-----------------------------------|------------------------------------------------------|
| GET    | `/health`                         | Engine + LLM configuration health check              |
| GET    | `/runs`                           | List all runs                                         |
| POST   | `/runs`                           | Start a new run `{ "prompt": string }`                |
| GET    | `/runs/{id}`                      | Full run state (poll this for the live dashboard)     |
| POST   | `/runs/{id}/chat`                 | `{ "agent": string, "question": string }`             |
| GET    | `/runs/{id}/checkpoints`          | List checkpoints                                      |
| POST   | `/runs/{id}/rollback`             | `{ "checkpoint_id": string }`                         |
| POST   | `/runs/{id}/debug`                | `{ "question": string }` — Natural Language Debugger  |
| GET    | `/runs/{id}/download`             | Download the run as a ZIP                             |

## Configuration reference (`.env`)

| Variable | Default | Meaning |
|---|---|---|
| `LLM_PROVIDER` | `openai` | Provider family (any OpenAI-compatible API) |
| `OPENAI_API_KEY` | *(required)* | Your API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model name |
| `OPENAI_BASE_URL` | *(empty = official OpenAI)* | Set to use OpenRouter/Groq/local etc. |
| `LLM_TEMPERATURE` | `0.3` | Sampling temperature |
| `LLM_MAX_TOKENS` | `2000` | Default max tokens per call |
| `LLM_TIMEOUT_SECONDS` | `120` | Maximum wait for any single LLM call |
| `LLM_MAX_RETRIES` | `2` | OpenAI-client retries for transient network errors |
| `MAX_BUILD_RETRIES` | `3` | Self-healing retries for install/start failures |
| `MAX_TEST_RETRIES` | `3` | Self-healing retries for failing QA tests |
| `MAX_DEBATE_ROUNDS` | `3` | Max rounds in Supervisor Debate Mode |
| `HEALTH_CHECK_TIMEOUT_SECONDS` | `30` | How long to wait for the deployed app to respond |
| `DEPLOY_PORT_RANGE_START` / `_END` | `4100` / `4200` | Port range used for generated apps |
| `AGENT_ENGINE_PORT` | `8000` | Port this FastAPI server listens on |
| `WORKSPACE_DIR` | `./workspace` | Where run artifacts are stored |

## Deploying this engine

### Option A — plain process (systemd/pm2/tmux)

```bash
cd python-agents
source .venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8000
```

Put that behind `systemd`, `pm2`, or a `tmux`/`screen` session for a simple
long-running deployment.

### Option B — Docker

```bash
cd python-agents
docker build -t forge-ai-agent-engine .
docker run --rm -p 8000:8000 --env-file .env forge-ai-agent-engine
```

> The generated apps are deployed **inside the container** on the port
> range you configured. If you need to open them from your host browser,
> publish that whole range, e.g. `-p 4100-4200:4100-4200`.

### Option C — docker-compose (whole stack)

See the root `docker-compose.yml`, which runs Postgres, this agent engine,
and the Next.js dashboard together with one command.

## Troubleshooting

- **"LLM is not configured" errors** — you haven't set `OPENAI_API_KEY` in
  `python-agents/.env`. Copy `.env.example` → `.env` and fill it in, then
  restart the server.
- **Deployment keeps failing after all retries** — open
  `workspace/<run_id>/server.log` and `workspace/<run_id>/docs/backend_implementation.md`
  to see exactly what the generated server does and why it's crashing;
  the Backend Agent's patch attempts are recorded as new commits in
  `state.json`.
- **QA agent appears to hang on test/edge-case generation** — the LLM call
  now respects `LLM_TIMEOUT_SECONDS` (default 120s). If generation still
  times out, the QA Agent writes deterministic fallback smoke/fuzz tests
  and continues instead of blocking the pipeline.
- **Port already in use** — widen/shift `DEPLOY_PORT_RANGE_START/END`.
- **CORS errors calling this API directly from a browser** — set
  `CORS_ORIGINS` to your dashboard's origin (defaults to `*`).
