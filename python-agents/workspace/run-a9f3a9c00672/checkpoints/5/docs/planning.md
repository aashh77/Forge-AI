# Agent Execution Plan

## Summary
Generate static site → audit security → run tests → reviewer approval → deploy to Netlify.

## Schedule

### step1 — frontend (generate)
- **Reason:** Initial build of the static front‑end is required before any security or testing can be performed.
- **Context:** Static JAMstack Catalogue architecture
- **Instructions:** Use Eleventy to compile the static site from markdown and JSON catalogue data, producing HTML/CSS/JS files.
- **Depends on:** none

### step2 — security (audit)
- **Reason:** Even static sites can contain client‑side vulnerabilities; auditing early ensures a secure build.
- **Context:** Static site with no backend
- **Instructions:** Run a security audit on the generated static files to check for XSS, CSP issues, and other client‑side vulnerabilities.
- **Depends on:** step1

### step3 — qa (test)
- **Reason:** Testing ensures functional requirements are met before review and deployment.
- **Context:** Static site with Eleventy
- **Instructions:** Execute automated tests (unit and integration) to verify catalogue display, filtering, responsiveness, and load performance (<200 ms).
- **Depends on:** step2

### step4 — reviewer (review)
- **Reason:** Human review catches issues that automated tests may miss and confirms aesthetic goals.
- **Context:** Static JAMstack Catalogue
- **Instructions:** Manually review the site for design consistency, theme appropriateness, and overall quality.
- **Depends on:** step3

### step5 — deploy (deploy)
- **Reason:** Final step to make the catalogue live after all checks are passed.
- **Context:** Netlify deployment of Eleventy site
- **Instructions:** Deploy the static files to Netlify, configuring the CDN and ensuring global availability.
- **Depends on:** step4

