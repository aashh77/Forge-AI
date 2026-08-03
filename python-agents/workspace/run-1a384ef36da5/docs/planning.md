# Agent Execution Plan

## Summary
The schedule executes a pure frontend workflow starting with static asset generation, followed by a security audit, QA testing, architectural review, and static deployment configuration. The backend agent is strictly omitted per the ADR.

## Schedule

### step_1 — frontend (generate)
- **Reason:** Generates the complete frontend user interface and visual animations requested by the user.
- **Context:** The chosen architecture uses a Static Client-Side SPA with HTML5 Canvas and CSS animations, omitting any backend.
- **Instructions:** Build a standalone static web application (HTML5, CSS3, Vanilla JavaScript) featuring a solid black background, centered white 'Hello World' text, a CSS-animated twinkling stars background layer, and an HTML5 Canvas particle physics system simulating colorful firecrackers/fireworks in the background.
- **Depends on:** none

### step_2 — security (audit)
- **Reason:** Validates the client-side code security posture before deployment.
- **Context:** Ensures the static SPA is completely self-contained and secure.
- **Instructions:** Audit the generated static files for any unintended external resource loads, insecure scripts, or best practice violations.
- **Depends on:** step_1

### step_3 — qa (test)
- **Reason:** Confirms visual requirements and client-side performance criteria are met.
- **Context:** Ensures high quality and performance compliance for the visual greeting page.
- **Instructions:** Perform static code analysis and verify that all HTML, CSS, and JS components render correctly and handle canvas animations smoothly.
- **Depends on:** step_1, step_2

### step_4 — reviewer (review)
- **Reason:** Guarantees adherence to the architectural decision record (ADR).
- **Context:** Final sanity check to ensure no backend code was mistakenly introduced and that requirements are fully satisfied.
- **Instructions:** Conduct a final code and architectural compliance review against the chosen Static Client-Side SPA option.
- **Depends on:** step_3

### step_5 — deploy (generate)
- **Reason:** Prepares the static app for final distribution.
- **Context:** The architecture specifies a static web host deployment.
- **Instructions:** Configure a static file server configuration to serve the generated SPA correctly.
- **Depends on:** step_4

