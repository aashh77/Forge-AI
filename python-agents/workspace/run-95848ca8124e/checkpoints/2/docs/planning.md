# Agent Execution Plan

## Summary
The schedule orchestrates the creation, security audit, QA testing, code review, supervisory debate, and deployment of a static coffee shop catalogue site, with security and QA running in parallel after generation.

## Schedule

### step1 — frontend (generate)
- **Reason:** Create the core static assets required for the catalogue.
- **Context:** Architecture Decision Record: Static Coffee Shop Catalogue – No Backend
- **Instructions:** Generate a static coffee shop catalogue site using HTML, CSS (Tailwind), vanilla JavaScript, and a bundled JSON catalog file. Ensure responsive layout, WCAG 2.1 AA compliance, and coffee-themed styling (brown, cream, espresso).
- **Depends on:** none

### step2 — security (audit)
- **Reason:** Static sites can still be vulnerable to XSS or insecure content; audit ensures compliance with security CTQs.
- **Context:** Architecture Decision Record: Static Coffee Shop Catalogue – No Backend
- **Instructions:** Audit the generated static site for security best practices: verify HTTPS usage, implement a Content Security Policy, ensure no insecure content is loaded, and confirm that the JSON data is served securely.
- **Depends on:** step1

### step3 — qa (test)
- **Reason:** Validate that the site meets all functional and accessibility CTQs.
- **Context:** Architecture Decision Record: Static Coffee Shop Catalogue – No Backend
- **Instructions:** Run functional tests to confirm all 50+ coffee items display correctly, perform responsive tests across mobile and desktop breakpoints, and run accessibility tests to meet WCAG 2.1 AA.
- **Depends on:** step1

### step4 — reviewer (review)
- **Reason:** Ensure the final product is clean, maintainable, and aligns with the chosen architecture.
- **Context:** Architecture Decision Record: Static Coffee Shop Catalogue – No Backend
- **Instructions:** Review the codebase for quality, maintainability, and adherence to the architecture decision. Verify that the styling, JavaScript, and JSON data are correctly implemented.
- **Depends on:** step2, step3

### step5 — supervisor (debate)
- **Reason:** Provide a final governance check before deployment.
- **Context:** Architecture Decision Record: Static Coffee Shop Catalogue – No Backend
- **Instructions:** Debate the overall architecture and deployment strategy to confirm alignment with business goals and cost constraints.
- **Depends on:** step4

### step6 — deploy (generate)
- **Reason:** Deliver the final static site to production.
- **Context:** Architecture Decision Record: Static Coffee Shop Catalogue – No Backend
- **Instructions:** Generate deployment configuration for Netlify (or similar CDN), push the static files, and verify the live deployment is accessible and correctly serves the catalogue.
- **Depends on:** step5

