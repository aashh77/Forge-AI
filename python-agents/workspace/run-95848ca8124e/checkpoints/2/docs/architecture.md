# Architecture Decision Record

## Request
build a simple web page with a catalogue for a coffee shop with appropriate coffee themes.

## Option 1: Static Site with JSON Data
A purely static website that loads coffee catalog data from a bundled JSON file, rendered client‑side with vanilla JavaScript.

**Components:** HTML, CSS (Sass or Tailwind), JavaScript (ES6 modules), JSON catalog file, Static web server (Netlify/Vercel/GitHub Pages)

**Pros:** Zero server‑side complexity; Fast load times via CDN; Easy CI/CD with Git; No runtime costs; Simple to host and maintain

**Cons:** Catalog changes require a redeploy; No built‑in admin UI; Limited scalability if catalog grows very large

**CTQ:** Responsive layout for mobile and desktop; Accessibility WCAG 2.1 AA; Catalog contains at least 50 coffee items; Theme colors reflect coffee branding (brown, cream, espresso)

## Option 2: Static Frontend with Serverless API
A static front‑end that fetches coffee catalog data from a lightweight serverless API backed by a NoSQL database.

**Components:** HTML, CSS (Sass or Tailwind), JavaScript (React/Vue), Serverless function (Netlify Functions/AWS Lambda), NoSQL database (DynamoDB/Firestore), API Gateway

**Pros:** Dynamic catalog updates without redeploy; Potential admin UI via API; Scalable data layer; Fine‑grained access control

**Cons:** Increased complexity and cost; Requires IAM or API keys; Deployment pipeline more involved

**CTQ:** API rate limits at least 1000 requests per day; Secure API endpoints (CORS, auth); Database schema supports coffee attributes (name, roast, price, description); Frontend caches API responses for performance

## Decision
Chosen: **option1**

The request is for a simple catalogue page; a static site meets all functional requirements with minimal complexity, cost, and deployment effort. Adding a backend would be unnecessary overhead.

## ADR
# Architecture Decision Record

## Title
Static Coffee Shop Catalogue – No Backend

## Status
✅ Approved

## Context
The client needs a simple web page displaying a coffee shop catalogue with coffee‑themed styling. No user authentication, dynamic content updates, or complex business logic are required.

## Decision
Deploy a purely static site that loads a bundled JSON catalog file and renders it client‑side. The site will be built with vanilla JS (or a lightweight framework if desired) and served from a CDN such as Netlify.

## Consequences
* **Pros** – Zero server maintenance, instant CDN caching, trivial CI/CD.
* **Cons** – Catalog updates require a redeploy; no built‑in admin UI.
* **Future work** – If dynamic updates become necessary, a lightweight serverless API can be added later.

---

## Alternatives Considered
1. **Static site + serverless API** – More complex, unnecessary for current scope.
2. **Full‑stack Express app** – Overkill and adds maintenance burden.

## Rationale
The simplest architecture that satisfies the functional requirements is chosen to reduce time‑to‑market and operational overhead.


## Diagram
```mermaid
graph TD
    A[User] --> B[Browser]
    B --> C[CDN (Netlify)]
    C --> D[HTML/CSS/JS]
    D --> E[JSON Catalog]
    E --> D
```
