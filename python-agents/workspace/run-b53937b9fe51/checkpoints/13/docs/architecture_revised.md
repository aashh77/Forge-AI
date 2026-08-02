# Revised Architecture

**Reason:** Adopt a serverless architecture (e.g., Next.js API routes, Firebase Functions, or Supabase) implementing the JWT‑HttpOnly cookie strategy with short‑lived access tokens and rotating refresh tokens, configure provisioned concurrency or warm‑up to keep cold‑start latency low, and use built‑in provider security controls for a secure, scalable solution.

**Chosen:** option1

## Justification
Next.js provides a unified framework for both frontend and API routes, simplifying development. Firebase Auth offers mature JWT handling and easy integration with short‑lived tokens and rotating refresh tokens. Firestore provides flexible schema for cart items. Vercel's provisioned concurrency ensures low latency. This stack aligns closely with the reviewer’s recommendation and offers rapid prototyping.

## ADR
# Architecture Decision Record\n\n## Context\nThe client requires a coffee catalogue web page with cart functionality. The reviewer recommends a serverless architecture with JWT‑HttpOnly cookie strategy, short‑lived access tokens, rotating refresh tokens, and low cold‑start latency.\n\n## Decision\nWe choose a **Next.js + Firebase Auth + Vercel** stack. Next.js API routes serve as serverless functions, Firebase Auth manages JWTs with short‑lived access tokens and rotating refresh tokens, and Vercel provides provisioned concurrency.\n\n## Consequences\n- **Pros**: Unified framework, rapid development, Firebase’s mature auth, Vercel’s low latency.\n- **Cons**: Firestore is NoSQL; may need schema design for cart.\n\n## Alternatives\n1. Supabase Edge Functions + Supabase Auth + Vercel.\n2. Serverless functions on AWS Lambda with Cognito.\n\n## Status\nAccepted.\n\n---\n\n## Implementation Notes\n- Store access token in HttpOnly cookie with `SameSite=Lax`.\n- Store refresh token in secure HttpOnly cookie.\n- Use Firebase Admin SDK in API routes to verify tokens.\n- Cart data stored in Firestore under `carts/{userId}`.\n- Configure Vercel’s `vercel.json` for provisioned concurrency.
