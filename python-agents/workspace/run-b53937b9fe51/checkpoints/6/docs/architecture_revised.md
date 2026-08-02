# Revised Architecture

**Reason:** Adopt the full‑stack REST API (option2) to ensure secure, validated cart handling and enable future payment and user account features.

**Chosen:** option2

## Justification
Option2 provides secure, validated cart handling, protects against tampering, and lays the groundwork for user accounts and payment processing. The REST API separates concerns, enabling independent scaling of frontend and backend services and simplifying future feature additions.

## ADR
# Architecture Decision Record (ADR)
## Context
The client requires a coffee catalogue web page with cart functionality. The reviewer recommends a full‑stack REST API to ensure secure, validated cart handling and future extensibility.
## Decision
Adopt a full‑stack REST API architecture (Option2).
## Consequences
- **Pros**: Secure cart operations, easy integration of authentication and payment, clear separation of concerns, scalable.
- **Cons**: Increased complexity, requires backend hosting and database setup.
## Alternatives
- Option1: Static SPA with localStorage cart. Simpler but insecure and not future‑proof.
## Rationale
Security and validation are critical for cart data. A REST API allows server‑side checks, prevents client tampering, and supports user accounts and payments.

