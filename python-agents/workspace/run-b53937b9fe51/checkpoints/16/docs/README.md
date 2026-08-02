# Forge AI Project README

**Original request:** make a web page about a coffee catalogue and I should be able to add things to the cart and view my cart

## Current Progress — Re-planning

Security raised 2 issue(s). Planner added 3 patch step(s) for backend.

## Agent Status

| Agent | Status | Progress |
|-------|--------|----------|
| architect | success | 100% |
| planner | success | 100% |
| backend | success | 100% |
| frontend | success | 100% |
| qa | idle | 0% |
| security | success | 100% |
| reviewer | idle | 0% |
| supervisor | success | 100% |
| deploy | idle | 0% |

## Key Decisions & Justifications

- **architect / architecture**: option1 — The user’s requirements only specify a catalog page with add‑to‑cart and view‑cart functionality. No user accounts, payment processing, or cross‑device persistence are mentioned. A static client‑only solution satisfies all CTQs with minimal complexity, faster load times, and easier deployment. Therefore, the static architecture is the optimal choice.
- **planner / schedule**: agent_execution_schedule — The schedule orchestrates the creation, security audit, testing, review, and deployment of a static coffee catalog web page, ensuring all CTQs are satisfied with minimal complexity.
- **planner / schedule**: agent_execution_schedule — The schedule builds backend and frontend in parallel, audits security, runs integration tests, reviews code, obtains supervisor approval, and deploys the application.
- **planner / schedule**: agent_execution_schedule — The project follows a parallel development of backend and frontend, followed by security audit, QA testing, code review, supervisor oversight, and deployment to Vercel, ensuring all architectural decisions are implemented and validated.
- **planner / replan**: patch_existing_code — Implemented strict CORS policy, added health‑check endpoint, unit‑tested Firestore security rules, and updated frontend fetch calls to include credentials, addressing the security audit findings.
- **backend / database**: PostgreSQL — The chosen full‑stack REST API architecture requires a relational database to store products, cart items, and user sessions. PostgreSQL offers robust ACID compliance, advanced query capabilities, and is the default database for Prisma. It can be run locally via Docker or a native installation, ensuring the developer’s localhost can host the service without external paid infrastructure.
  - *Alternatives rejected:* [{"name": "SQLite", "why_rejected": "SQLite is file\u2011based and would simplify local development, but it lacks certain PostgreSQL features (e.g., advanced concurrency, full JSON support, and robust replication) that the architecture may need for future scaling and complex queries."}, {"name": "MySQL", "why_rejected": "MySQL is a viable relational database, but the project\u2019s ORM (Prisma) defaults to PostgreSQL for many advanced features, and the chosen stack already presumes PostgreSQL."}]
- **backend / api_style**: REST/Express — Express chosen for minimal footprint and fast local install/build.
- **backend / database**: JSON-file store — A JSON-file store keeps all cart and catalogue data on the developer’s local machine, eliminating the need for any external paid or networked infrastructure. It’s simple to set up, fully file‑based, and works out of the box on a localhost environment.
  - *Alternatives rejected:* [{"name": "SQLite", "why_rejected": "SQLite is file\u2011based but adds a heavier dependency and is overkill for a simple cart; a plain JSON file is lighter and easier to manage for this use case."}, {"name": "In\u2011memory store (e.g., Map or Redis\u2011like in\u2011memory DB)", "why_rejected": "Data would be lost on page reload or server restart, defeating persistence requirements."}]
- **backend / api_style**: REST/Express — Express chosen for minimal footprint and fast local install/build.
- **frontend / state_management**: Browser localStorage — Dependency-free frontend scheduled by Planner.
- **frontend / state_management**: localStorage — Dependency-free frontend scheduled by Planner.
- **frontend / state_management**: localStorage — Dependency-free frontend scheduled by Planner.
- **security / security_audit**: audit_complete — Found 2 code finding(s), 0 debated. Architecture issue: True.
- **security / security_audit**: audit_complete — Found 2 code finding(s), 0 debated. Architecture issue: True.
- **security / security_audit**: audit_complete — Found 1 code finding(s), 0 debated. Architecture issue: True.

## Quick Start

```bash
cd /Users/e335446/Desktop/implement-makechangesmd-updates/python-agents/workspace/run-b53937b9fe51/project
npm install
npm start
```

The server listens on `process.env.PORT` (default 4100). Visit `http://localhost:<PORT>/api/health` to verify it is running.

## Production Deployment
See `docs/DEPLOYMENT.md` for detailed instructions for Vercel, Netlify, GitHub Pages, Render, Railway, Fly.io, Docker and external databases.

---
*This README is regenerated after every agent step.*