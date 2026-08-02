# Forge AI

An autonomous software-engineering dashboard. Type what you want built, click **Forge It**, and watch a team of specialised AI agents design, build, test, secure, review and deploy it.

---

## What This Project Is

Forge AI is a full-stack application with two main parts:

1. **Next.js Dashboard** (`src/`) — the UI where you enter prompts, watch agents work, inspect decisions, chat with agents, and download the generated project.
2. **Python Agent Engine** (`python-agents/`) — a FastAPI service that runs the multi-agent pipeline, generates code, runs tests and deploys the result locally.

The agents are:
- **Architect** — picks the tech stack and writes an Architecture Decision Record.
- **Planner** — schedules the other agents.
- **Backend** — builds the Express backend when needed.
- **Frontend** — builds the vanilla HTML/CSS/JS UI.
- **QA** — writes and runs smoke/fuzz tests.
- **Security** — audits code and live headers.
- **Reviewer** — checks requirements and commits.
- **Supervisor** — resolves conflicts and scores reliability.
- **Deploy** — runs the generated project on localhost.

---

## Prerequisites

- **Node.js 20+** and **npm**
- **Python 3.11+**
- **PostgreSQL** (local or cloud; the app reads `DATABASE_URL` from `.env`)
- An **OpenAI API key** (or an OpenAI-compatible provider and base URL)

---

## Quick Start

### 1. Install dashboard dependencies

```bash
npm install
```

### 2. Configure the database

Create a Postgres database and set the connection string:

```bash
# .env
DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:5432/app_db"
AGENT_API_URL="http://127.0.0.1:8000"
```

Push the schema:

```bash
npx drizzle-kit push
```

### 3. Configure the agent engine

```bash
cd python-agents
cp .env.example .env
```

Edit `python-agents/.env`:

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
# Optional:
# OPENAI_BASE_URL=https://...
# LLM_PROVIDER=openai
```

Create a Python virtual environment and install dependencies:

```bash
cd python-agents
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Start the agent engine

```bash
cd python-agents
python server.py
```

The engine runs on `http://127.0.0.1:8000` by default.

### 5. Start the dashboard

In another terminal from the project root:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## 5-Minute Vercel Deploy

You can deploy the dashboard to Vercel and point it at a hosted Postgres instance.

1. **Push the repo to GitHub** (only the root Next.js project needs to be deployed; Vercel will detect it).
2. **Create a project on Vercel** and import the repo.
3. **Set environment variables** in Vercel:
   - `DATABASE_URL` — your Postgres connection string.
   - `AGENT_API_URL` — URL of your running agent engine (e.g., a fly.io/render/EC2 instance).
4. **Deploy.** Vercel runs `npm run build` automatically.

> Note: the Python agent engine must be hosted separately; Vercel only runs the Next.js frontend/API. For a quick self-hosted demo you can run everything on your own machine.

---

## Web Speech Notes

The dashboard has a microphone button next to the prompt input.

- **English (`en-US`)** is transcribed directly into the prompt box.
- **Hindi (`hi-IN`)** is transcribed and then translated to English by the agent engine while preserving intent. The original Hindi and an intent note are shown below the prompt.
- Speech recognition requires a browser that supports the Web Speech API (Chrome/Edge are the most reliable). If the browser does not support it, an alert is shown.

The translation endpoint is `/api/forge/translate`, which proxies to the agent engine so your API key never reaches the browser.

---

## How Codex Built It

I started from a simple idea: turn a user request into a complete, running application with full transparency. The implementation follows three principles:

1. **Agents should be observable.** Every agent writes logs, decisions and commits to a shared run state that the dashboard polls and renders live. Nothing is hidden.
2. **Generated code should run locally.** The engine generates Node.js projects with minimal dependencies, adds missing health endpoints, and retries deployment until the app is reachable.
3. **The system should self-improve.** Security and Reviewer agents can trigger Supervisor debates or Planner replans, so the pipeline fixes its own mistakes instead of stopping.
4. **Every agent has a specific task.** Each agent is tasked with its own job which it carries out while keeping track of the whole cntext of the project. The agents are interconnected yet independent.

The frontend is Next.js with Tailwind CSS. State is stored in PostgreSQL via Drizzle ORM. The agent engine is FastAPI with a custom LLM client that tracks cost, tokens and latency. All agent reasoning is real LLM output; there are no canned responses.

---

## Useful Commands

```bash
# Dashboard development
npm run dev

# Type check
npm run typecheck

# Lint
npm run lint

# Production build
npm run build

# Push schema changes
npx drizzle-kit push

# Run the agent engine
cd python-agents && python server.py
```

---

## Demo Project

A pinned **demo** project is included in the history. It simulates a complete run for the prompt:

> "Build a small webpage that shows a short poem with twinkling stars in the background."

The demo cannot be deleted and serves as an example of what a finished Forge AI run looks like, including agent logs, decisions, checkpoints, deployment preview and reliability stats.
