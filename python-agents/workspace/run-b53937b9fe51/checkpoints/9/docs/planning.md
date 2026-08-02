# Agent Execution Plan

## Summary
The schedule builds backend and frontend in parallel, audits security, runs integration tests, reviews code, obtains supervisor approval, and deploys the application.

## Schedule

### 1 — backend (generate)
- **Reason:** Establish server‑side logic for secure cart handling.
- **Context:** Backend implementation of REST API.
- **Instructions:** Generate backend code for product and cart endpoints using Express, TypeScript, Prisma, and JWT auth.
- **Depends on:** none

### 2 — frontend (generate)
- **Reason:** Provide user interface for catalog and cart.
- **Context:** Frontend UI for coffee catalogue.
- **Instructions:** Generate React SPA with product listing, cart UI, Redux Toolkit, and Material‑UI components.
- **Depends on:** none

### 3 — security (audit)
- **Reason:** Ensure server‑side security.
- **Context:** Backend security audit.
- **Instructions:** Audit backend code for security best practices: input validation, rate limiting, CORS, CSRF, HTTPS enforcement.
- **Depends on:** 1

### 4 — security (audit)
- **Reason:** Prevent client‑side vulnerabilities.
- **Context:** Frontend security audit.
- **Instructions:** Audit frontend code for security: XSS prevention, CSP, secure cookie handling, token storage.
- **Depends on:** 2

### 5 — qa (test)
- **Reason:** Validate functionality and security.
- **Context:** QA testing of full stack.
- **Instructions:** Perform integration tests: API endpoints, authentication flow, cart operations, frontend integration.
- **Depends on:** 3, 4

### 6 — reviewer (review)
- **Reason:** Ensure maintainability and compliance.
- **Context:** Code review.
- **Instructions:** Review code quality, architecture adherence, and test coverage.
- **Depends on:** 5

### 7 — supervisor (review)
- **Reason:** Final approval before deployment.
- **Context:** Supervisor approval.
- **Instructions:** Final sign‑off on architecture and readiness for deployment.
- **Depends on:** 6

### 8 — deploy (generate)
- **Reason:** Make application available to users.
- **Context:** Deployment.
- **Instructions:** Deploy backend to AWS Elastic Beanstalk, frontend to Vercel, configure database on RDS.
- **Depends on:** 7

