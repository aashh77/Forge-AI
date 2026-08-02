# Architecture Decision Record

## Request
Build a webpage that says hello world in white text with black background and twinkling stars in the background and allows you to trigger a small burst animation when you click a button called click me.

## Option 1: Pure Static Frontend
A single-page application using only HTML, CSS, and vanilla JavaScript to render a black background with white "Hello World" text, twinkling stars, and a button that triggers a burst animation.

**Components:** index.html, styles.css, script.js, assets/ (optional)

**Pros:** Zero server‑side complexity – instant load times; Easy deployment to static hosts (GitHub Pages, Netlify, Vercel); No runtime environment required; Full control over animation performance via CSS/Canvas

**Cons:** Cannot add server‑side features (e.g., analytics, user auth) without refactoring; No built‑in caching beyond CDN; Limited to client‑side storage if needed

**CTQ:** Performance (frame rate of animation); Cross‑browser compatibility (Chrome, Firefox, Safari, Edge); Accessibility (WCAG 2.1 AA); Maintainability (clear separation of concerns)

## Option 2: Static Frontend with Lightweight Node.js Server
Serve the same static assets via an Express.js server, allowing future expansion to API endpoints or server‑side rendering.

**Components:** server.js, public/index.html, public/styles.css, public/script.js, public/assets/

**Pros:** Future‑proof for adding APIs or authentication; Can run server‑side logic if needed; Deployable on Heroku, Render, or any Node runtime; Can serve over HTTPS without external CDN

**Cons:** Adds deployment complexity and runtime cost; Requires Node.js environment; Increases attack surface; Higher latency for static content compared to CDN

**CTQ:** Server uptime; API scalability; Security (CORS, Helmet); Deployment pipeline complexity

## Decision
Chosen: **option1**

The user’s requirements are fully satisfied by a purely static solution: no server‑side logic is needed, and a static site delivers the fastest load times and simplest deployment. Adding a backend would only increase complexity without providing immediate benefits.

## ADR
# Architecture Decision Record

## Context
The requested application is a single page that displays "Hello World" in white text on a black background, shows twinkling stars, and plays a burst animation when a button is clicked. No user data, authentication, or server‑side processing is required.

## Decision
We will implement the application as a **Pure Static Frontend** using only HTML, CSS, and vanilla JavaScript.

## Alternatives
1. **Static Frontend with Lightweight Node.js Server** – would allow future API endpoints but adds unnecessary complexity for the current scope.
2. **Full‑stack framework (React + Express)** – overkill for a single page and would increase bundle size and build complexity.

## Consequences
- **Pros**: Zero server maintenance, instant deployment to static hosts, minimal bundle size, excellent performance.
- **Cons**: No built‑in server‑side features; any future backend logic would require refactoring.

## Rationale
The application is purely presentational. A static site meets all functional requirements, keeps the codebase minimal, and simplifies deployment. If future features require server logic, the architecture can be extended later.

---

## Decision Status
✅ Adopted

---

## Related Decisions
None.


## Diagram
```mermaid
graph TD
  A[Browser] -->|HTTP GET| B[HTML/CSS/JS]
  B --> C[Render "Hello World" text]
  B --> D[Canvas/CSS for twinkling stars]
  B --> E[Button click event]
  E --> F[Trigger burst animation]
  subgraph Assets
    B --> G[styles.css]
    B --> H[script.js]
    B --> I[assets/]
  end
```
