# Agent Execution Plan

## Summary
Single-pass schedule for a static frontend-only page: Architect chooses the stack, Frontend generates the page, QA validates it, Security audits it, Reviewer checks requirements, Deploy serves it.

## Schedule

### step-1 — frontend (generate)
- **Reason:** The chosen architecture has no backend; the Frontend Agent produces the complete static page.
- **Context:** Static HTML/CSS/JS page with twinkling star background and a poem.
- **Instructions:** Generate public/index.html, public/styles.css and public/app.js. Use CSS animations for twinkling stars. Keep the markup accessible and mobile-friendly.
- **Depends on:** none

### step-2 — qa (test)
- **Reason:** Verify the static page loads and the health endpoint responds.
- **Context:** Run smoke tests against the locally deployed static server.
- **Instructions:** Generate tests/smoke.mjs and tests/fuzz.mjs. Assert root returns 200 and /api/health returns { status: "ok" }.
- **Depends on:** step-1

### step-3 — security (audit)
- **Reason:** Confirm there are no secrets, dependencies or XSS vectors in a purely static page.
- **Context:** Static files with no external dependencies.
- **Instructions:** Scan for hardcoded secrets and review headers/content.
- **Depends on:** step-2

### step-4 — reviewer (review)
- **Reason:** Validate that the generated page satisfies the user's exact request.
- **Context:** Review the poem text, star animation and mobile layout.
- **Instructions:** Approve if the page displays a poem and twinkling stars on mobile and desktop.
- **Depends on:** step-3

### step-5 — deploy (generate)
- **Reason:** Serve the static project locally so the dashboard can preview it.
- **Context:** Final deployment step.
- **Instructions:** Start the static server on a free localhost port and verify GET /api/health.
- **Depends on:** step-4
