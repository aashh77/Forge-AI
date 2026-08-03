# Forge AI Deployment Guide

**Generated for:** build a simple web page with a catalogue for a coffee shop with appropriate coffee themes.

**Architecture:** option1 — The user request is for a simple web page with a coffee shop catalogue. A static JAMstack site satisfies all functional requirements (display, filter, responsive design) while keeping the architecture minimal, cost‑free, and easy to deploy. Adding a backend would introduce unnecessary complexity and maintenance overhead for a feature that can be served statically.

**API style:** static JSON
**Deployment target:** Netlify
**Has backend:** no

## Local Development

```bash
cd /Users/e335446/Desktop/implement-makechangesmd-updates(LATEST-FINAL)/python-agents/workspace/run-a9f3a9c00672/project
npm install
npm start
```

The server listens on `process.env.PORT` (default `4100`).

## Database — in-memory / JSON file

This project uses an embedded or in-memory store. No external database server is required. Data is persisted to JSON files or lives only for the lifetime of the process.


### Vercel

1. Import the `project/public` folder (or drag-and-drop in the dashboard).
2. Framework preset: **Other**.
3. The publish directory is `public/`.
4. Add any required environment variables under **Settings > Environment Variables**.

### Netlify

1. Create a new site and deploy the `project/public` folder.
2. Build command: leave empty.
3. Publish directory: `public/`.

### GitHub Pages

1. Push the `project/public` contents to a repository.
2. Enable GitHub Pages from the repository settings.
3. Choose the branch/folder that contains the static files.

## Health Verification

Once the server is running, verify it with:
```bash
curl http://localhost:4100/api/health
```

Live deployment URL recorded by Forge AI: `http://localhost:4100`

Run the generated smoke tests (if available) with:
```bash
npx vitest run
npx playwright test
```

## Environment Variables

| Variable | Required | Notes |
|----------|----------|-------|
| `PORT` | ✅ | Used by generated server |


## Run Signals

- QA status: `success`
- Deployment status: `unknown`
- Reliability average: `72.2`
- Estimated bugs: `2`

---
*This guide is generated automatically by Forge AI and reflects the final checkpoint.*