# Forge AI Agents

Forge AI is driven by a multi-agent engine. Each agent is a specialised collaborator that owns one phase of the software-engineering lifecycle. They share a common base class (`python-agents/agents/base.py`) for logging, decisions, commits and LLM calls, but implement their own reasoning and actions.

---

## Agent Catalogue

### 1. Architect Agent (`agents/architect.py`)
**Role:** First mover. Decides the high-level architecture and tech stack.

**What it does:**
- Produces two genuinely distinct architecture options.
- Compares them on components, pros/cons and CTQs (Critical-To-Quality attributes).
- Chooses the simplest architecture that satisfies the request and is allowed to omit the backend when the request is purely presentational.
- Writes an Architecture Decision Record (`docs/architecture.md`) and a Mermaid diagram.

**Key outputs:**
- Decision: `topic="architecture"`
- Document: `docs/architecture.md`
- Commit: ADR file

**Entry point:** `run(user_request: str) -> dict`

---

### 2. Planner Agent (`agents/planner.py`)
**Role:** Schedules the work for the other agents.

**What it does:**
- Reads the Architect's decision.
- Builds an execution schedule of steps with `agent`, `action`, `depends_on`, `instructions`, `context`, `reason`.
- Injects a `deploy` step automatically if the LLM forgets one.
- Can be re-activated later (`replan`) to patch code after a downstream agent finds an issue.

**Key outputs:**
- Decision: `topic="schedule"` or `topic="replan"`
- Document: `docs/planning.md` (or `docs/replan.md`)

**Entry points:** `create_schedule(...)`, `replan(...)`

---

### 3. Backend Agent (`agents/backend.py`)
**Role:** Builds the server-side API when the architecture includes a backend.

**What it does:**
- Chooses a datastore biased toward embedded/file-based or in-memory stores for zero-external-infrastructure localhost runs.
- Generates a Node.js/Express backend with `express` and `cors` as the only dependencies.
- Ensures `server.js` listens on `process.env.PORT`, serves static files and exposes `GET /api/health`.
- Can patch its own previously generated code via `apply_patch`.

**Key outputs:**
- Decision: `topic="database"`, `topic="api_style"`
- Files: `server.js`, `package.json`, backend routes
- Document: `docs/backend_implementation.md`, `docs/backend_database_justification.md`

**Entry points:** `run(...)`, `generate(...)`, `apply_patch(...)`

---

### 4. Frontend Agent (`agents/frontend.py`)
**Role:** Builds the user interface.

**What it does:**
- Generates a vanilla HTML/CSS/JS frontend (no framework, no build step) under `public/`.
- When there is a backend, wires the UI to relative `/api/...` routes.
- When there is no backend, keeps all state in the browser (`localStorage`, in-memory, etc.).
- Enforces basic accessibility (semantic HTML, labels, ARIA, focus states).
- Can patch its own code via `apply_patch`.

**Key outputs:**
- Decision: `topic="state_management"`
- Files: `public/index.html`, `public/styles.css`, `public/app.js`
- Document: `docs/frontend.md`

**Entry points:** `run(...)`, `generate(...)`, `apply_patch(...)`

---

### 5. QA Agent (`agents/qa.py`)
**Role:** Tests the generated application.

**What it does:**
- Generates `tests/smoke.mjs` and `tests/fuzz.mjs` using Node's global `fetch`.
- Runs smoke tests against the live deployment.
- Runs fuzz/exploratory requests.
- Performs a code-quality review and produces a score.
- Falls back to deterministic tests if LLM generation fails.

**Key outputs:**
- Decision: `topic="code_quality"`
- Files: `tests/smoke.mjs`, `tests/fuzz.mjs`
- Documents: `docs/qa_report.md`, `docs/quality_review.md`

**Entry points:** `generate_tests(...)`, `execute_tests(base_url)`, `fuzz(base_url)`, `quality_check(...)`

---

### 6. Security Agent (`agents/security.py`)
**Role:** Audits the codebase and live deployment for security issues.

**What it does:**
- Scans for hardcoded secrets with regex patterns.
- Runs `npm audit --json` when `node_modules` exists.
- Reviews architecture-level and code-level findings.
- Flags issues that need a Supervisor debate vs. issues that can be patched directly.
- Performs dynamic header analysis on the running deployment.
- Auto-fixes leaked secrets when safe to do so.

**Key outputs:**
- Decision: `topic="security_audit"`, `topic="data_access_pattern"`
- Documents: `docs/security_audit_report.md`, `docs/security_static_report.md`, `docs/security_dynamic_report.md`

**Entry points:** `audit(...)`, `run_static(...)`, `run_dynamic(base_url)`, `apply_patch(...)`

---

### 7. Reviewer Agent (`agents/reviewer.py`)
**Role:** Validates the whole output against the original request.

**What it does:**
- Reviews the codebase against the user prompt and architecture.
- Checks whether requirements are met, architecture is adequate, and what changes are needed.
- Reviews every commit from every agent and computes an overall PR acceptance percentage.

**Key outputs:**
- Decisions: `topic="requirements_review"`, `topic="code_review"`
- Documents: `docs/requirements_review.md`, `docs/review.md`
- Stats: `pr_acceptance_pct`

**Entry points:** `review_codebase(...)`, `run()`

---

### 8. Supervisor Agent (`agents/supervisor.py`)
**Role:** Mediates conflicts and produces final reliability metrics.

**What it does:**
- Detects conflicting decisions across agents (e.g., backend vs. security on datastore).
- Runs short, focused LLM debates (max 3 rounds, stops early on concession).
- Records the full transcript and verdict in `docs/debate_<topic>_<ts>.md`.
- Scores the AI Reliability Scorecard from observed signals (deployment success, QA status, retries, debates, project size).
- Computes final run statistics (latency, tokens, cost, regression history).

**Key outputs:**
- Decisions: `topic="reliability"`
- Documents: `docs/reliability_scorecard.md`, debate transcripts
- Stats: `compilation_success_pct`, `tests_passed_pct`, `reliability_avg`, etc.

**Entry points:** `detect_and_resolve_conflicts()`, `mediate_dispute(...)`, `mediate_architecture_security(...)`, `score_reliability()`, `compute_final_stats()`

---

### 9. Deploy Agent (handled by `builder.py`)
**Role:** Actually runs the generated project on localhost.

**What it does:**
- This is not a class in `agents/`; the pipeline calls `builder.py` for the deploy step.
- Determines whether the project has a backend or is static.
- Creates a fallback static server for frontend-only projects.
- Runs `npm install` when needed.
- Starts the server on a free port in the configured range.
- Repeatedly health-checks `GET /api/health` until the app is live or retries are exhausted.
- Stores deployment URL, status and logs in the run state.

**Key outputs:**
- `deployment` object in the run state
- `server.log` in `workspace/<run>/`

**Key file:** `python-agents/builder.py`

---

## Orchestration

The `PipelineExecutor` in `python-agents/pipeline.py` coordinates everything:
1. Run Architect.
2. Run Planner to produce a schedule respecting dependencies.
3. Execute the schedule by multi-agent softwarre developers.
4. After the code developement, run the Reviewer's requirements review.
5. Run Supervisor scoring and final stats. If any multi-agent conflict arises, Supervisor will resolve it.

Security findings can trigger a Supervisor debate or a Planner replan. The user can pause, resume or stop a run from the dashboard; control flags are checked between steps.

---


## Shared Infrastructure

### `BaseAgent` (`agents/base.py`)
Every agent inherits from `BaseAgent`, which provides:
- **Logging** — `log(message, level)` writes timestamped entries to the run state.
- **Status & progress** — `status(status, progress)` updates the dashboard bars.
- **Decisions** — `decide(topic, chosen, justification, **extra)` records why an agent chose a path.
- **Commits** — `commit(message, files)` records file-level deliverables.
- **File I/O** — `write_file(rel_path, content)` writes into `workspace/<run>/project/`; `write_doc(filename, content)` writes into `workspace/<run>/docs/`.
- **LLM helpers** — `ask_json(system, user, ...)` and `ask_text(...)` call the configured LLM through `llm_client`.
- **Chat & Debug** — `answer_question(question)` powers the dashboard's per-agent Q&A; `trace(question, layer_description)` powers the Natural Language Debugger.

All LLM calls are real calls to the provider configured in `python-agents/.env` (`OPENAI_API_KEY`, etc.). There are no canned responses.

---

## General Notes (by Codex)

- All agents use the **same LLM client** and **same cost/token tracking**.
- All agent states, logs, decisions, commits, checkpoints and debates are stored in `workspace/<run>/state.json` and mirrored to Postgres for the Next.js dashboard.
- Agents can be asked direct questions from the dashboard; answers are grounded only in that agent's own recorded decisions, logs and commits.
