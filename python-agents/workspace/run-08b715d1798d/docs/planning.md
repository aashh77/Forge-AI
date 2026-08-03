# Agent Execution Plan

## Summary
The project follows a linear workflow: generate frontend, audit security, test, review, and deploy.

## Schedule

### step1 — frontend (generate)
- **Reason:** Generate the core static content as per the chosen architecture.
- **Context:** Architecture Decision Record: Static HTML/CSS on CDN. No backend required.
- **Instructions:** Create a single static HTML file with inline CSS that sets a black background and white text displaying "Hello World".
- **Depends on:** none

### step2 — security (audit)
- **Reason:** Validate that the static assets meet security best practices before deployment.
- **Context:** Architecture Decision Record: Static site served via CDN. Must be accessible via HTTPS.
- **Instructions:** Perform a security audit on the generated HTML/CSS to ensure compliance with HTTPS delivery, no inline scripts, and proper MIME types.
- **Depends on:** step1

### step3 — qa (test)
- **Reason:** Ensure functional and visual correctness across target environments.
- **Context:** Architecture Decision Record: Static site on CDN. Responsive to user agent.
- **Instructions:** Run automated visual regression tests to confirm the page renders correctly on various browsers and devices, and verify that the text is readable against the black background.
- **Depends on:** step2

### step4 — reviewer (review)
- **Reason:** Human oversight to catch any issues missed by automated tests.
- **Context:** Architecture Decision Record: Static site on CDN. Must be accessible via HTTPS.
- **Instructions:** Manually review the HTML/CSS for accessibility (WCAG), correct color contrast, and overall quality.
- **Depends on:** step3

### step5 — deploy (deploy)
- **Reason:** Deploy the final static asset to the chosen CDN-hosted platform.
- **Context:** Deployment target: GitHub Pages. No backend deployment needed.
- **Instructions:** Publish the static HTML file to GitHub Pages, ensuring the repository is configured for HTTPS and the file is served from the root path.
- **Depends on:** step4

