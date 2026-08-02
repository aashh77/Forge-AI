# Agent Execution Plan

## Summary
The project follows a parallel development of backend and frontend, followed by security audit, QA testing, code review, supervisor oversight, and deployment to Vercel, ensuring all architectural decisions are implemented and validated.

## Schedule

### step1 — backend (generate)
- **Reason:** Backend API routes provide serverless functions for cart operations, aligning with the chosen stack and ensuring secure access via Firebase Auth.
- **Context:** Architecture Decision Record: Next.js + Firebase Auth + Vercel stack chosen.
- **Instructions:** Generate Next.js API routes for cart CRUD operations, integrate with Firestore, and implement Firebase Auth middleware for token verification.
- **Depends on:** none

### step2 — frontend (generate)
- **Reason:** Frontend components are independent of the backend code and can be developed in parallel, providing the UI for catalog and cart.
- **Context:** Architecture Decision Record: Next.js + Firebase Auth + Vercel stack chosen.
- **Instructions:** Generate Next.js pages and React components for the coffee catalogue, cart view, and add-to-cart functionality, using Firebase Auth for user state and HttpOnly cookie for access token handling.
- **Depends on:** none

### step3 — security (audit)
- **Reason:** Security audit must examine the backend implementation to confirm compliance with the chosen authentication strategy.
- **Context:** Architecture Decision Record: JWT‑HttpOnly cookie strategy with short‑lived access tokens and rotating refresh tokens.
- **Instructions:** Audit the JWT handling in the backend API routes, verify HttpOnly cookie usage, short‑lived access token expiry, and rotating refresh token flow, ensuring no XSS or CSRF vulnerabilities.
- **Depends on:** step1

### step4 — qa (test)
- **Reason:** QA testing validates that both backend and frontend work together correctly and that security measures function as intended.
- **Context:** Architecture Decision Record: Next.js + Firebase Auth + Vercel stack chosen.
- **Instructions:** Run integration tests covering cart CRUD endpoints, token refresh flow, and frontend interactions (add to cart, view cart). Include end‑to‑end tests using Cypress or Playwright.
- **Depends on:** step1, step2, step3

### step5 — reviewer (review)
- **Reason:** Reviewer ensures the implementation meets the architectural goals and quality standards.
- **Context:** Architecture Decision Record: Next.js + Firebase Auth + Vercel stack chosen.
- **Instructions:** Review the codebase for architectural consistency, adherence to the ADR, and best practices in Next.js, Firebase Auth, and Firestore usage.
- **Depends on:** step4

### step6 — supervisor (review)
- **Reason:** Supervisor provides the final gatekeeping step before production deployment.
- **Context:** Architecture Decision Record: Next.js + Firebase Auth + Vercel stack chosen.
- **Instructions:** Perform final oversight, confirm all ADR requirements are satisfied, and approve the code for deployment.
- **Depends on:** step5

### step7 — deploy (generate)
- **Reason:** Deployment finalizes the project, ensuring low latency and proper configuration per the ADR.
- **Context:** Architecture Decision Record: Next.js + Firebase Auth + Vercel stack chosen.
- **Instructions:** Deploy the Next.js application to Vercel with provisioned concurrency, configure environment variables for Firebase project, and set up Vercel build settings.
- **Depends on:** step6

