# Agent Execution Plan

## Summary
Sequential build pipeline: generate static frontend → security audit → QA testing → reviewer review → deploy to Netlify.

## Schedule

### step1 — frontend (generate)
- **Reason:** Frontend must be built first to provide the code for subsequent security audit, testing, and deployment.
- **Context:** Architecture option1: Static HTML/CSS/JS with JSON Catalogue
- **Instructions:** Create a static coffee‑themed webpage using HTML, CSS (Tailwind), vanilla JS, and a local JSON file for the catalogue. Ensure responsive design and client‑side search functionality.
- **Depends on:** none

### step2 — security (audit)
- **Reason:** Security audit must precede testing and deployment to catch vulnerabilities early.
- **Context:** Static site, no backend, but still requires client‑side security best practices.
- **Instructions:** Run a security audit on the generated static assets. Verify no inline scripts, enforce CSP headers, check for XSS vectors, and ensure all assets are served over HTTPS.
- **Depends on:** step1

### step3 — qa (test)
- **Reason:** QA testing ensures functional and performance requirements are met before review.
- **Context:** Static site with client‑side catalogue.
- **Instructions:** Execute automated tests: unit tests for JS functions, accessibility checks (aXe), responsive layout tests, and performance benchmarks (<200 ms load).
- **Depends on:** step2

### step4 — reviewer (review)
- **Reason:** Human review catches design and content issues that automated tests may miss.
- **Context:** Completed QA pass.
- **Instructions:** Manually review UI/UX, coffee theme consistency, catalogue accuracy, and overall polish. Provide feedback for any final tweaks.
- **Depends on:** step3

### step5 — deploy (deploy)
- **Reason:** Deployment is the last step after all checks and reviews are complete.
- **Context:** Final approved static assets.
- **Instructions:** Deploy the static site to Netlify, configuring build settings to serve the JSON catalogue and enable HTTPS. Verify deployment success and correct URL.
- **Depends on:** step4

