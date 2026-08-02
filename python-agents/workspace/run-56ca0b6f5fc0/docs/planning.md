# Agent Execution Plan

## Summary
Generate Hugo site, patch styling, audit security, test QA, review design, score CTQs, then deploy to Netlify.

## Schedule

### step1 — frontend (generate)
- **Reason:** Initial content and structure must be created before any modifications or checks.
- **Context:** Static JAMstack catalog architecture
- **Instructions:** Use Hugo to scaffold the static site with a coffee‑themed layout and generate pages from Markdown and YAML data files.
- **Depends on:** none

### step2 — frontend (patch)
- **Reason:** Styling is a CTQ; patching ensures visual consistency before security or QA.
- **Context:** Styling and asset optimization
- **Instructions:** Apply CSS/SCSS theme overrides to ensure a cohesive coffee‑themed UI and optimize images for performance.
- **Depends on:** step1

### step3 — security (audit)
- **Reason:** Even static sites can be vulnerable to XSS or misconfigured headers; audit early to catch issues.
- **Context:** Static site security best practices
- **Instructions:** Run a static security audit (e.g., OWASP ZAP for static assets, check CSP headers, ensure no exposed secrets in source).
- **Depends on:** step2

### step4 — qa (test)
- **Reason:** Ensures functional correctness and SEO friendliness before review.
- **Context:** Quality assurance for static content
- **Instructions:** Perform manual and automated UI tests: verify all catalogue items render, links work, responsive design, and SEO meta tags are present.
- **Depends on:** step3

### step5 — reviewer (review)
- **Reason:** Human review catches subtle issues that automated tests may miss.
- **Context:** Final stakeholder approval
- **Instructions:** Conduct a final design and content review, checking coffee theme consistency, accessibility, and overall user experience.
- **Depends on:** step4

### step6 — supervisor (score)
- **Reason:** Supervisor validates that all CTQs are met before deployment.
- **Context:** Project quality metrics
- **Instructions:** Score the project against CTQs: catalog consistency, theme styling, SEO, and zero downtime deployment.
- **Depends on:** step5

### step7 — deploy (generate)
- **Reason:** Final step to make the site live; depends on all prior approvals.
- **Context:** Deployment to CDN
- **Instructions:** Build the final Hugo site, generate static files, and deploy to Netlify CDN with edge caching and automatic HTTPS.
- **Depends on:** step6

