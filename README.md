# Forge AI - Multi-Modal Agentic AI Application

Forge AI is a full-stack application of a multi-modal and multi-agent software engineering system. A Next.js dashboard orchestrates a Python "agent engine" that runs eight specialised agents — Architect, Planner, Backend, Frontend, QA, Security, Reviewer and Supervisor — to design, build, test, secure, review and **deploy** a runnable project from a single natural-language prompt.

Just type what you want to build or speak to it, explain your application, and click **Forge It** to watch a team of specialised AI agents that are fired to design, build, test, review, self-heal and auto-deploy it.


---

## What This Project Is

Forge AI is a full-stack application with two main parts:

1. **Next.js Dashboard** (`src/`) — the UI where you can enter prompts, watch the agents work, inspect their decisions, chat with agents, and download the generated project.
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
- **Deploy** — runs and deploys the generated project.

---

## Special Feature - Multi-Agent Conflict Resolution:
The Supervisor Agent is activated when a conflict or disagreement arises between any of the agents. It facilitates a structured debate by allowing the agents to present and defend their viewpoints, challenge assumptions, and provide supporting evidence. If any arguments are unclear, incomplete, or ambiguous, the Supervisor Agent asks targeted clarification questions. After evaluating the facts, reasoning, evidence, and logical consistency of the arguments, it makes the final decision and selects the most appropriate course of action.

### For example: Security Agent vs Architecture Agent Conflict Resolution
When a conflict occurs between the Security Agent and the Architecture Agent, the Supervisor Agent evaluates both arguments and makes a decision based on technical feasibility, impact, risk, and project requirements.

Case 1: Architecture Agent loses: 
- The Supervisor Agent determines that the proposed architecture is insufficient or flawed based on security, scalability, performance, or other constraints. 
- The architecture must be redesigned.
- The pipeline is restarted and replanned.

Case 2: Security Agent loses

- The Supervisor Agent determines that the current architecture is acceptable and that security concerns do not justify architectural changes.
- The Security Agent is asked to identify possible improvements that can be applied without modifying the overall architecture.
- These security recommendations are forwarded to the Planner Agent, which incorporates them into the implementation plan.


---


## Prerequisites

- **Node.js 20+** and **npm**
- **Python 3.11+**
- **PostgreSQL**
- **OpenAI API key**

---

## Quick Start 

### Local deployment

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

### 5-Minute Vercel Deploy

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

Codex started from a simple idea: turn a user request into a complete, running application with full transparency. The implementation follows four principles:

1. **Agents should be observable.** Every agent writes logs, decisions and commits to a shared run state that the dashboard polls and renders live. Nothing is hidden.
2. **Generated code should run locally.** The engine generates Node.js projects with minimal dependencies, adds missing health endpoints, and retries deployment until the app is reachable.
3. **The system should self-improve.** Security and Reviewer agents can trigger Supervisor debates or Planner replans, so the pipeline fixes its own mistakes instead of stopping.
4. **Every agent has a specific task.** Each agent is tasked with its own job which it carries out while keeping track of the whole cntext of the project. The agents are interconnected yet independent.

The frontend is Next.js with Tailwind CSS. State is stored in PostgreSQL via Drizzle ORM. The agent engine is FastAPI with a custom LLM client that tracks cost, tokens and latency. All agent reasoning is real LLM output; there are no canned responses.

---

## Demo Project

A pinned **demo** project is included in the history. It simulates a complete run for the prompt:

> "Build a small webpage that shows a short poem with twinkling stars in the background."

The demo cannot be deleted and serves as an example of what a finished Forge AI run looks like, including agent logs, decisions, checkpoints, deployment preview and reliability stats.

---

## Codex Prompts

### 1.
Create  agent AI code using Python for below defined task. Also, provide steps to run and deploy the agent AI codebase.

The Problem
Developers don't need another coding chatbot. They need an AI engineering team. Today AI writes code. Tomorrow AI builds software. Forge AI demonstrates exactly that.

The Idea
Imagine opening GitHub. Instead of "Generate function"
You say "Build authentication with OAuth, RBAC, audit logs, tests and deployment." Then...
Instead of ONE AI...7 specialised AI agents wake up.

Architect Agent 1
Designs the architecture. Produces architecture diagrams. Writes ADRs. Provide option1 and option 2 architecture with pros and cons of each option. Highlight CTQ for each option.

Planner Agent 2
Breaks project into issues. Provide and justify the breaking and creation of issues. Creates dependency graph. Creates at least 2 options of schedules and list the pros and cons of each schedule. Choose best schedule among options available and then Schedules execution.

Backend Agent 3
Builds APIs. Choose which Database to use and creat justification document. Create database
Create Business logic.

Frontend Agent 4
Builds UI. Provide configuration for user
State management.
Accessibility.

QA Agent 5
Generates
        * tests
        * edge cases
        * fuzz tests
Runs them.
Keeps fixing until green.

Security Agent 6
Runs
OWASP checks
Dependency scan
Secrets detection
Permission analysis
Threat modelling
Fixes issues automatically.

Reviewer Agent 7
Reviews every commit.
Explains why.
Suggests improvements.
Rejects bad PRs.

Every agent AI is visible to user. Every agent produce justification documents for decisions taken and list conditions for every major or minor decision taken. We literally watch software being built in a dashboard.

The dashboard shows status of all agents (status bar graph with color Red if it had issues in running, Green if running smoothly, blue if waiting/pending due to dependency).

On dashboard, Click bar graph such as Backend and show another detailed status like backend agent is working.

Now make backend agent answerable to questions( so add chat option for user to ask questions).

Create a Supervisor AI agent that watches every other AI agent. This agent will resolve all disputes.If two agents disagree.

Every agent AI decision becomes a checkpoint. This will help in rollback to previous checkpoint in case testing or security fails or security is flagged as risk(self healing feature).

Finally add AI reliability dashboard. Every action of all agent AI gets scored.

Finally, The dashboard must show stats about the AI agents like toke usage, cost.

One more feature in dashboard to add is Natural Language Debugger where in User can type issues and then all agents go back and trace the issues and start analysing and fixing their part and show status on dashboard for each decision taken to fix issue. Creates incident report with all fixes as checkpoint.

### 2.
The architect must decide the architecture(the tech stack, ADR, CTQs of various options, diagrams and the framework) fully. 

Planner only assigns the tasks to the other agents AND decides which agent goes first, does what task and which agent after that. It schedules the other agents. It can also make two agents work simultaneously, or make one agent do partial work then switch to another agent before coming back to the previous agent and finishing the task. The full scheduling is handled by the planner. (EXAMPLE: it might schedule a security check in middle of the backend, or it may activate the frontend before security). It must schedule the agents according to the whole context available. If it has been re-activated later on(EXAMPLE: by the security agent, it must schedule ACCORDING to the changes that need to be made AND supply the agents the already existing code(so full new code need not be generated) with the issue flagged so that issue can be rectified in the EXISTING code)

The security agent must go through the WHOLE code created when it is activated. It must figure out the vulnerabilities. It must forward the vulnerabilities to the appropriate agent(EXAMPLE: if the backend is not secure enough, send the issue and vulnerability to the planner agent. The planner agent reviews and re-schedules the backend AND the frontend(as if backend is changed, the frontend might change as well) BUT not with empty context, but with the pre-existing code and tells them to change what the security flagged. Essentially, dont re-write the code, but just make the changes needed). The security agent might figure out code vulnerabilities OR some issues with the base architecture selected(by the architecture agent initially) , in which case, it will flag it. This goes ahead into a debate scenario with the architecture agent(overseen by the supervisor) in which the two agents explain their reasoning, counter each other's points and the supervisor chooses the better logic. If security wins, architecture is restart and has to use a new tech stack or such as suggested by security. If security loses, the NORMAL workflow is resumed. (EXAMPLE: architecture chose react for a project but security figures out that this particular use case has vulnerabilities and instead wants to switch onto vue). Overall, if basic architecture has a problem, counter the architecture agent. If a code vulnerability is found(EXAMPLE: frontend exposes some sensitive data) then inform planner s planner agent can reorganize to rectify)

Supervisor agent is activated when a clash occurs between ANY two agents. It lets them argue a few points, asks for clarification if some points are obscure, and then takes the better decision based on the facts and arguments and logic it is presented. It should have the full knowledge of the agentic pipeline so it can assign the losing agent to make the changes and restart the pipeline(IF NEEDED). For example, if in security vs architecture, architecture loses->reschedule architecture(which means the whole pipeline must be restarted as if the architecture of the project is changed, all the code must be re-written). if security loses-> ask security to suggest some changes that can be made in existing architecture to improve security(if any significant improvement is possible. if no significant improvement can be made in security, juts move the pipeline normally) and dump that into planner agent.

The QA agent runs all the edge tests and fuzz tests and such, but also keeps the user informed in detail about what it is doing, what the result is and all.


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


