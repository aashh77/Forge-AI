# Architecture Decision Record

## Request
build a simple web page with a black background and white text saying hello world

## Option 1: Static HTML/CSS served by CDN
Serve a single HTML file with inline CSS from a CDN or static file server.

**Components:** HTML file, CSS, CDN/static server

**Pros:** Zero server cost; Fast delivery via edge caching; Simple to deploy

**Cons:** No dynamic content; Limited interactivity

**CTQ:** Must be a single page; No server-side logic required

## Option 2: Node.js Express server
Minimal Express app that serves the hello world page.

**Components:** Node.js runtime, Express framework, HTML template

**Pros:** Extensible for future features; Easy to add API endpoints; Local development with nodemon

**Cons:** Requires a runtime environment; Higher deployment cost; More maintenance

**CTQ:** Need to handle HTTP requests; Server must be running

## Decision
Chosen: **option1**

The requirement is a static page with no dynamic behavior. A static CDN-hosted page is the simplest, most cost-effective solution.

## ADR
# Architecture Decision Record\n\n## Status\nProposed\n\n## Context\nThe application is a single-page web page with a black background and white \"Hello World\" text. No dynamic content or server-side logic is required.\n\n## Decision\nUse a static HTML/CSS file served from a CDN or static hosting service (e.g., Netlify, GitHub Pages, Cloudflare Pages). No custom backend is necessary.\n\n## Consequences\n- **Pros**: Zero server maintenance, instant global delivery, minimal cost.\n- **Cons**: Cannot support future dynamic features without adding a backend.\n- **Future**: If dynamic behavior is needed, a lightweight backend can be added later.\n

## Diagram
```mermaid
graph TD;\n  User[\"User\"] -->|HTTP GET /| CDN[\"CDN / Static Server\"];\n  CDN -->|Serve HTML/CSS| User;
```
