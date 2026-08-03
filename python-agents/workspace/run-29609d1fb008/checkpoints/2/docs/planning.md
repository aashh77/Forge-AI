# Agent Execution Plan

## Summary
The schedule orchestrates static page generation, security audit, QA testing, review, supervisor debate, and deployment in a linear sequence, with QA and security running in parallel after generation.

## Schedule

### 1 — frontend (generate)
- **Reason:** Frontend generation is the first step to produce the artifact to be audited, tested, reviewed, and deployed.
- **Context:** Architecture decision: static HTML/CSS served by CDN.
- **Instructions:** Create a single HTML file with inline CSS that sets a black background and white 'Hello World' text.
- **Depends on:** none

### 2 — security (audit)
- **Reason:** Security audit must run on the produced code before it is reviewed or deployed.
- **Context:** Static page with no dynamic content; audit ensures no client‑side vulnerabilities.
- **Instructions:** Perform a security audit of the generated HTML/CSS, checking for XSS vectors, CSP compliance, and best‑practice headers.
- **Depends on:** 1

### 3 — qa (test)
- **Reason:** QA testing can proceed independently of the security audit once the code is generated.
- **Context:** Ensures visual correctness and WCAG compliance for the simple page.
- **Instructions:** Run automated visual regression tests and accessibility checks on the static page.
- **Depends on:** 1

### 4 — reviewer (review)
- **Reason:** Review must wait for both security and QA to complete.
- **Context:** Final human verification before deployment.
- **Instructions:** Manually review the audit report and QA results, confirming that the page meets all requirements.
- **Depends on:** 2, 3

### 5 — supervisor (debate)
- **Reason:** Supervisor debate is the last decision point before production.
- **Context:** Governance step to confirm compliance with ADR.
- **Instructions:** Debate the final readiness of the project, ensuring all stakeholders agree on deployment.
- **Depends on:** 4

### 6 — deploy (generate)
- **Reason:** Deployment occurs after all checks and approvals are complete.
- **Context:** Deployment to CDN as per architecture decision.
- **Instructions:** Package the HTML/CSS into a static file bundle and deploy to the chosen CDN (e.g., Netlify).
- **Depends on:** 5

